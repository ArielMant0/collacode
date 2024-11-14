export function sortObjByString(attribute, options={ ascending: true, ignoreCase: true }) {
    return function(a, b) {
        const sA = options.ignoreCase ? a[attribute].toLowerCase() : a[attribute]
        const sB = options.ignoreCase ? b[attribute].toLowerCase() : a[attribute]
        if (sA < sB) { return options.ascending ? -1 : 1; }
        if (sA > sB) { return options.ascending ? 1 : -1; }
        // must be equal
        return 0;
    }
}