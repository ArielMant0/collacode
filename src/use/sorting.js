export function sortObjByString(attribute, options={ ascending: true, ignoreCase: true }) {
    return function(a, b) {
        const sA = options.ignoreCase ? a[attribute].toLowerCase() : a[attribute]
        const sB = options.ignoreCase ? b[attribute].toLowerCase() : b[attribute]
        if (sA < sB) { return options.ascending ? -1 : 1; }
        if (sA > sB) { return options.ascending ? 1 : -1; }
        // must be equal
        return 0;
    }
}

export function sortObjByValue(attribute, options={ ascending: true, ignoreCase: true }) {
    return function(a, b) {
        const sA = a[attribute]
        const sB = b[attribute]
        if (sA < sB) { return options.ascending ? -1 : 1; }
        if (sA > sB) { return options.ascending ? 1 : -1; }
        // must be equal
        return 0;
    }
}

export function sortObjMultiple(attributes, options={ ascending: true, ignoreCase: true }) {
    return function(a, b) {
        for (let i = 0; i < attributes.length; ++i) {
            let func;
            switch (attributes[i].type) {
                case "string":
                    func = sortObjByString(attributes[i].name, options)
                    break
                default:
                    func = sortObjByValue(attributes[i].name, options)
            }
            const val = func(a, b)
            if (val !== 0) {
                return val
            }
        }
        // must be equal
        return 0;
    }
}