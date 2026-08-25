
export function cosine(a, b) {
    if (a.length !== b.length) return undefined;
    let n = a.length;
    let sum = 0;
    let sum_a = 0;
    let sum_b = 0;
    let all_same = true;
    for (let i = 0; i < n; ++i) {
        sum += a[i] * b[i];
        sum_a += a[i] * a[i];
        sum_b += b[i] * b[i];
        all_same = all_same && a[i] === b[i]
    }

    return all_same ? 0 : Math.acos(sum / (Math.sqrt(sum_a) * Math.sqrt(sum_b)));
}

export function euclidean(a, b) {
    const val = euclidean_squared(a, b)
    return val ? Math.sqrt(val) : undefined
}

export function euclidean_squared(a, b) {
    if (a.length !== b.length) return undefined
    let n = a.length;
    let sum = 0;
    for (let i = 0; i < n; ++i) {
        sum += (a[i] - b[i]) ** 2;
    }
    return sum
}

export function jaccard(a, b, exact_equal=true) {
    let int = 0, union = 0;
    let n = a.length;
    for (let i = 0; i < n; ++i) {
        int += a[i] !== 0 && (!exact_equal || a[i] === b[i]) ? 1 : 0
        union += a[i] !== 0 || b[i] !== 0 ? 1 : 0
    }
    return 1 - (union > 0 ? int / union : 0)
}

export function getMetric(metric) {
    switch (metric) {
        case "euclidean": return euclidean
        case "jaccard": return jaccard
        case "cosine": return cosine
        default: return euclidean_squared
    }
}