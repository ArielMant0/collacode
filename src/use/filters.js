export const FILTER_TYPES = Object.freeze({
    VALUE: 0,
    SET_OR: 1,
    SET_AND: 2,
    RANGE_IN_IN: 3,
    RANGE_EX_EX: 4,
    RANGE_IN_EX: 5,
    RANGE_EX_IN: 6,
})

function l(a, b) { return a < b }
function le(a, b) { return a <= b }

function g(a, b) { return a > b }
function ge(a, b) { return a >= b }

export function makeFilter(type, key, attr, values=null) {
    switch (type) {
        default:
        case FILTER_TYPES.VALUE:
            return new Filter(key, attr, values)
        case FILTER_TYPES.SET_OR:
            return new SetOrFilter(key, attr, values)
        case FILTER_TYPES.SET_AND:
            return new SetAndFilter(key, attr, values)
        case FILTER_TYPES.RANGE_IN_IN:
        case FILTER_TYPES.RANGE_EX_EX:
        case FILTER_TYPES.RANGE_IN_EX:
        case FILTER_TYPES.RANGE_EX_IN:
            return new RangeFilter(key, attr, values, type)
    }
}

export function isSetFilter(type) {
    return type === FILTER_TYPES.SET_AND || type === FILTER_TYPES.SET_OR
}
export function isRangeFilter(type) {
    return type === FILTER_TYPES.RANGE_IN_IN ||
        type === FILTER_TYPES.RANGE_EX_EX ||
        type === FILTER_TYPES.RANGE_IN_EX ||
        type === FILTER_TYPES.RANGE_EX_IN
}

export class Filter {

    constructor(key, attr, value=null) {
        this.type = FILTER_TYPES.VALUE;
        this.key = key;
        this.attr = attr;
        this.set(value)
    }

    get size() {
        return this.value !== null ? 1 : 0
    }

    asArray() {
        return [this.value]
    }

    getValue(datum) {
        switch(typeof this.attr) {
            case "function": return this.attr(datum);
            default: return datum[this.attr];
        }
    }

    empty() {
        return this.size === 0;
    }

    clear() {
        this.set(null)
    }

    toggle(value) {
        this.set(this.value === value ? null : value)
    }

    set(value) {
        this.value = value;
    }

    matches(datum) {
        const v = this.getValue(datum)
        switch(typeof v) {
            default: return v === this.value;
            case "function": return v() === this.value;
            case "object":
                if (Array.isArray(v)) {
                    return v.includes(this.value)
                }
                if (v instanceof Set) {
                    return v.has(this.value)
                }
                return Object.values(v).includes(this.value)
        }
    }
}

export class SetOrFilter extends Filter {

    constructor(key, attr, value=[]) {
        super(key, attr)
        this.type = FILTER_TYPES.SET_OR;
        this.value = new Set()
        this.set(value)
    }

    get size() {
        return this.value.size
    }

    asArray() {
        return Array.from(this.value.values())
    }

    getData() {
        return this.value
    }

    clear() {
        this.value.clear();
    }

    _toggle(value) {
        if (this.value.has(value)) {
            this.value.delete(value)
        } else {
            this.value.add(value)
        }
        this.array = Array.from(this.value.values())
    }

    toggle(value) {
        switch(typeof value) {
            default: return this._toggle(value);
            case "function": return this.toggle(value())
            case "object":
                if (Array.isArray(value)) {
                    return value.forEach(d => this._toggle(d))
                }
                if (value instanceof Set) {
                    return value.forEach(d => this._toggle(d))
                }
                return Object.values(value).some(d => this._toggle(d))
        }
    }

    set(value) {
        this.value = value instanceof Set ?
            value :
            new Set(Array.isArray(value) ? value : [value])
        this.array = Array.from(this.value.values())
    }

    _matches(v) {
        switch(typeof v) {
            default: return this.value.has(v);
            case "function": return this._matches(v())
            case "object":
                if (Array.isArray(v)) {
                    return this.array.some(d => v.includes(d))
                }
                if (v instanceof Set) {
                    return this.array.some(d => v.has(d))
                }
                const vals = Object.values(v)
                return this.array.some(d => vals.includes(d))
        }
    }

    matches(datum) {
        return this._matches(this.getValue(datum))
    }

}

export class SetAndFilter extends SetOrFilter {

    constructor(key, attr, value=[]) {
        super(key, attr, value)
        this.type = FILTER_TYPES.SET_AND;
    }

    _matches(v) {
        switch(typeof v) {
            default: return this.value.has(v);
            case "function": return this._matches(v())
            case "object": {
                if (Array.isArray(v)) {
                    return this.array.every(d => v.includes(d))
                }
                if (v instanceof Set) {
                    return this.array.every(d => v.has(d))
                }
                const vals = Object.values(v)
                return this.array.every(d => vals.includes(d))
            }
        }
    }

    matches(datum) {
        return this._matches(this.getValue(datum))
    }
}

export class RangeFilter extends Filter {

    constructor(key, attr, value=[null, null], type=FILTER_TYPES.RANGE_IN_IN) {
        super(key, attr)
        this.type = type;
        switch (this.type) {
            default:
            case FILTER_TYPES.RANGE_IN_IN:
                this.compL = ge;
                this.compR = le;
                break;
            case FILTER_TYPES.RANGE_EX_EX:
                this.compL = g;
                this.compR = l;
                break;
            case FILTER_TYPES.RANGE_IN_EX:
                this.compL = ge;
                this.compR = l;
                break;
            case FILTER_TYPES.RANGE_EX_IN:
                this.compL = g;
                this.compR = le;
                break;
        }
        this.value = []
        this.set(value)
    }

    get size() {
        return this.value.length
    }

    asArray() {
        return this.value.slice()
    }

    empty() {
        return this.value.length === 0
    }

    clear() {
        this.value = [];
    }

    toggle(value) {
        if (!value || value[0] === null && value[1] === null) return this.clear()
        if (this.empty()) return this.set(value)

        const idx = this.value.findIndex(d => d[0] === value[0] && d[1] === value[1])
        if (idx >= 0) {
            this.value.splice(idx, 1);
        } else {
            this.value.push(value)
        }
    }

    set(value) {
        if (value && value.length > 0) {
            this.value = Array.isArray(value.at(0)) ?
                value.map(d => ([d.at(0), d.at(-1)])) :
                [value]
        } else {
            this.value = []
        }
    }

    _matches(v) {
        switch(typeof v) {
            default:
                return this.value.some(r => (r[0] === null || this.compL(v, r[0])) && (r[1] === null || this.compR(v, r[1])))
            case "function":
                return this._matches(v())
            case "object":
                if (Array.isArray(v)) {
                    return v.some(d => this.value.some(r => (r[0] === null || this.compL(d, r[0])) &&
                        (r[1] === null || this.compR(d, r[1]))))
                }
                if (v instanceof Set) {
                    return this._matches(Array.from(v.values()))
                }
                return this._matches(Object.values(v))
        }
    }

    matches(datum) {
        if (this.empty()) return false;
        return this._matches(this.getValue(datum))
    }
}
