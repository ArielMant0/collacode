import * as druid from '@saehrimnir/druidjs'

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
    if (a.length !== b.length) return undefined;
    let n = a.length;
    let sum = 0;
    for (let i = 0; i < n; ++i) {
        sum += (a[i] - b[i]) ** 2;
    }
    return Math.sqrt(sum)
}

export function euclidean_squared(a, b) {
    return druid.euclidean_squared(a, b)
}

export function getMetric(metric) {
    switch (metric) {
        case "cosine": return cosine
        default: return euclidean_squared
    }
}