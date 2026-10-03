package com.arcanaforensics.arcalume.core

import java.math.BigDecimal
import java.math.RoundingMode

/**
 * A small JSON model whose serializer produces the same bytes as Python's
 * `json.dumps(obj, sort_keys=True, separators=(",", ":"))` (ASCII-only output).
 *
 * Vault headers and custody-ledger hashes are computed over those bytes on the
 * desktop, so both apps must agree exactly. Numbers keep their original text when
 * parsed, so re-serializing a parsed ledger line never changes a digit.
 */
sealed class Json {
    object Null : Json()
    data class Bool(val value: Boolean) : Json()
    data class Num(val raw: String) : Json() {
        init { require(NUMBER.matches(raw)) { "not a JSON number: $raw" } }
        val long: Long get() = raw.toLong()
        val double: Double get() = raw.toDouble()
    }
    data class Str(val value: String) : Json()
    data class Arr(val items: List<Json>) : Json()
    data class Obj(val fields: Map<String, Json>) : Json() {
        operator fun get(key: String): Json? = fields[key]
    }

    fun str(): String = (this as? Str)?.value ?: throw JsonError("expected a string")
    fun long(): Long = (this as? Num)?.let { runCatching { it.long }.getOrNull() } ?: throw JsonError("expected an integer")
    fun obj(): Obj = this as? Obj ?: throw JsonError("expected an object")
    fun arr(): List<Json> = (this as? Arr)?.items ?: throw JsonError("expected an array")

    /** Canonical, Python-compatible encoding (sorted keys, no spaces, ASCII escapes). */
    fun canonical(): String = StringBuilder().also { write(it) }.toString()
    fun canonicalBytes(): ByteArray = canonical().toByteArray(Charsets.US_ASCII)

    private fun write(sb: StringBuilder) {
        when (this) {
            Null -> sb.append("null")
            is Bool -> sb.append(if (value) "true" else "false")
            is Num -> sb.append(raw)
            is Str -> quote(value, sb)
            is Arr -> { sb.append('['); items.forEachIndexed { i, v -> if (i > 0) sb.append(','); v.write(sb) }; sb.append(']') }
            is Obj -> {
                sb.append('{')
                // Python sorts by code point; Kotlin String comparison is by UTF-16 unit.
                // They agree except for astral characters, which never appear in our keys.
                fields.keys.sorted().forEachIndexed { i, k -> if (i > 0) sb.append(','); quote(k, sb); sb.append(':'); fields.getValue(k).write(sb) }
                sb.append('}')
            }
        }
    }

    companion object {
        private val NUMBER = Regex("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?")
        const val MAX_DEPTH = 64

        fun of(v: Any?): Json = when (v) {
            null -> Null
            is Json -> v
            is Boolean -> Bool(v)
            is Int, is Long, is Short -> Num(v.toString())
            is Double -> Num(pyFloat(v))
            is Float -> Num(pyFloat(v.toDouble()))
            is String -> Str(v)
            is Map<*, *> -> Obj(v.entries.associate { (k, x) -> k as String to of(x) })
            is Iterable<*> -> Arr(v.map { of(it) })
            else -> throw IllegalArgumentException("cannot encode ${v::class}")
        }

        fun obj(vararg pairs: Pair<String, Any?>): Obj = Obj(linkedMapOf(*pairs.map { it.first to of(it.second) }.toTypedArray()))

        fun parse(text: String): Json = Parser(text).parseDocument()
        fun parse(bytes: ByteArray): Json = parse(String(bytes, Charsets.UTF_8))

        private fun quote(s: String, sb: StringBuilder) {
            sb.append('"')
            for (c in s) {
                when {
                    c == '"' -> sb.append("\\\"")
                    c == '\\' -> sb.append("\\\\")
                    c == '\n' -> sb.append("\\n")
                    c == '\r' -> sb.append("\\r")
                    c == '\t' -> sb.append("\\t")
                    c == '\b' -> sb.append("\\b")
                    c == '\u000c' -> sb.append("\\f")
                    c.code < 0x20 || c.code > 0x7e -> sb.append("\\u").append(String.format(java.util.Locale.ROOT, "%04x", c.code))
                    else -> sb.append(c)
                }
            }
            sb.append('"')
        }

        /**
         * Python's repr() for a float that was rounded to at most [decimals] places,
         * e.g. 0.25 -> "0.25", 1.0 -> "1.0", 0.00005 -> "5e-05".
         */
        fun pyFloat(x: Double, decimals: Int = 6): String {
            require(x.isFinite()) { "JSON cannot hold $x" }
            val d = BigDecimal(x).setScale(decimals, RoundingMode.HALF_EVEN).stripTrailingZeros()
            if (d.signum() == 0) return if (x < 0 || (x == 0.0 && 1.0 / x < 0)) "-0.0" else "0.0"
            val abs = d.abs()
            if (abs < BigDecimal("0.0001")) {
                // repr switches to scientific notation below 1e-4: mantissa digits + e-XX
                val unscaled = abs.unscaledValue().toString()
                val exp = unscaled.length - 1 - abs.scale()
                val mant = if (unscaled.length == 1) unscaled else unscaled[0] + "." + unscaled.substring(1)
                return (if (d.signum() < 0) "-" else "") + mant + "e-" + String.format(java.util.Locale.ROOT, "%02d", -exp)
            }
            val plain = d.toPlainString()
            return if ('.' in plain) plain else "$plain.0"
        }
    }
}

class JsonError(msg: String) : IllegalArgumentException(msg)

private class Parser(private val s: String) {
    private var i = 0

    fun parseDocument(): Json {
        val v = value(0)
        ws()
        if (i != s.length) throw JsonError("trailing data at $i")
        return v
    }

    private fun ws() { while (i < s.length && s[i] in " \t\r\n") i++ }

    private fun value(depth: Int): Json {
        if (depth > Json.MAX_DEPTH) throw JsonError("nested too deeply")
        ws()
        if (i >= s.length) throw JsonError("unexpected end")
        return when (s[i]) {
            '{' -> obj(depth)
            '[' -> arr(depth)
            '"' -> Json.Str(string())
            't' -> lit("true", Json.Bool(true))
            'f' -> lit("false", Json.Bool(false))
            'n' -> lit("null", Json.Null)
            else -> num()
        }
    }

    private fun lit(word: String, v: Json): Json {
        if (!s.startsWith(word, i)) throw JsonError("bad literal at $i")
        i += word.length
        return v
    }

    private fun num(): Json {
        val start = i
        while (i < s.length && (s[i].isDigit() || s[i] in "+-.eE")) i++
        val raw = s.substring(start, i)
        return try { Json.Num(raw) } catch (e: IllegalArgumentException) { throw JsonError("bad number at $start") }
    }

    private fun string(): String {
        i++ // opening quote
        val sb = StringBuilder()
        while (true) {
            if (i >= s.length) throw JsonError("unterminated string")
            val c = s[i++]
            when {
                c == '"' -> return sb.toString()
                c == '\\' -> {
                    if (i >= s.length) throw JsonError("bad escape")
                    when (val e = s[i++]) {
                        '"', '\\', '/' -> sb.append(e)
                        'b' -> sb.append('\b'); 'f' -> sb.append('\u000c'); 'n' -> sb.append('\n')
                        'r' -> sb.append('\r'); 't' -> sb.append('\t')
                        'u' -> {
                            if (i + 4 > s.length) throw JsonError("bad unicode escape")
                            sb.append(s.substring(i, i + 4).toIntOrNull(16)?.toChar() ?: throw JsonError("bad unicode escape"))
                            i += 4
                        }
                        else -> throw JsonError("bad escape \\$e")
                    }
                }
                c.code < 0x20 -> throw JsonError("control character in string")
                else -> sb.append(c)
            }
        }
    }

    private fun arr(depth: Int): Json {
        i++
        val items = ArrayList<Json>()
        ws()
        if (i < s.length && s[i] == ']') { i++; return Json.Arr(items) }
        while (true) {
            items += value(depth + 1)
            ws()
            if (i >= s.length) throw JsonError("unterminated array")
            when (s[i++]) { ',' -> continue; ']' -> return Json.Arr(items); else -> throw JsonError("expected , or ]") }
        }
    }

    private fun obj(depth: Int): Json {
        i++
        val fields = LinkedHashMap<String, Json>()
        ws()
        if (i < s.length && s[i] == '}') { i++; return Json.Obj(fields) }
        while (true) {
            ws()
            if (i >= s.length || s[i] != '"') throw JsonError("expected key at $i")
            val k = string()
            ws()
            if (i >= s.length || s[i++] != ':') throw JsonError("expected :")
            if (fields.put(k, value(depth + 1)) != null) throw JsonError("duplicate key $k")
            ws()
            if (i >= s.length) throw JsonError("unterminated object")
            when (s[i++]) { ',' -> continue; '}' -> return Json.Obj(fields); else -> throw JsonError("expected , or }") }
        }
    }
}
