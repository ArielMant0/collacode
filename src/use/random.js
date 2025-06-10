import Chance from "chance"
import DM from "./data-manager"
import { range } from "d3"

const chance = new Chance()

export function randomLeafTags(size=1, minCount=1, ignore=[]) {
    const exclude = new Set(ignore)
    const tags = DM.getDataBy("tags", d => {
        return d.is_leaf === 1 &&
            !exclude.has(d.id) &&
            DM.getDataItem("tags_counts", d.id) >= minCount
    })
    return randomChoice(tags, size)
}

export function randomItems(size=1, minTags=1) {
    const items = DM.getDataBy("items", d => d.allTags.length >= minTags)
    return randomChoice(items, size)
}

export function randomItemsWithTags(tagIds, size=1) {
    const include = new Set(Array.isArray(tagIds) ? tagIds : [tagIds])
    const items = DM.getDataBy("items", d => d.allTags.find(t => include.has(t.id)))
    return randomChoice(items, size)
}

export function randomItemsWithoutTags(tagIds, size=1) {
    const exclude = new Set(Array.isArray(tagIds) ? tagIds : [tagIds])
    const items = DM.getDataBy("items", d => !d.allTags.find(t => exclude.has(t.id)))
    return randomChoice(items, size)
}

export function getItemsWithSimilarity(targets, ignore=[], weights=[]) {
    const no = new Set(ignore)
    targets = Array.isArray(targets) ? targets : [targets]
    targets.forEach(t => no.add(t.id))
    const items = DM.getDataBy("items", d => d.allTags.length > 0 && !no.has(d.id))
    const ts = targets.map(t => new Set(t.allTags.map(d => d.id)))
    return items.map(d => {
        const ds = new Set(d.allTags.map(t => t.id))
        const sims = ts.map(set => {
            const int = set.intersection(ds)
            const un = set.union(ds)
            return int.size / un.size
        })
        return {
            id: d.id,
            similarity: sims.reduce((acc, s) => acc + s, 0) / targets.length
        }
    })
}

export function randomItemsSimilar(targets, size=1, ignore=[], weights=[], mul=3) {
    let data = getItemsWithSimilarity(targets, ignore, weights)
    if (data.length > size * mul) {
        data.sort((a, b) => b.similarity - a.similarity)
        data = data.slice(0, size * mul)
    }
    const res = randomWeighted(data.map(d => d.id), data.map(d => d.similarity), size)
    const ids = new Set(size > 1 ? res : [res])
    const items = DM.getDataBy("items", d => ids.has(d.id))
    return items.length === 1 ? items[0] : items
}

export function randomItemsDissimilar(targets, size=1, ignore=[], weights=[], mul=3) {
    let data = getItemsWithSimilarity(targets, ignore, weights)
    data.forEach(d => d.similarity = 1 - d.similarity)
    if (data.length > size * mul) {
        data.sort((a, b) => b.similarity - a.similarity)
        data = data.slice(0, size * mul)
    }
    const res = randomWeighted(data.map(d => d.id), data.map(d => d.similarity), size)
    const ids = new Set(size > 1 ? res : [res])
    const items = DM.getDataBy("items", d => ids.has(d.id))
    return items.length === 1 ? items[0] : items
}

export function randomChoice(array, size=1) {
    return size < 2 ? chance.pickone(array) : chance.pickset(array, size)
}

export function randomWeighted(array, weights, size=1) {
    if (size < 2) {
        return chance.weighted(array, weights)
    }
    const r = []
    const o = array.slice(), w = weights.slice()
    while (r.length < size && o.length > 0) {
        const idx = chance.weighted(range(o.length), w)
        r.push(o[idx])
        o.splice(idx, 1)
        w.splice(idx, 1)
    }
    return r
}


export function randomShuffle(array) {
    return chance.shuffle(array)
}

export function randomInteger(min, max) {
    const opts = {}
    if (min !== undefined) { opts.min = min }
    if (max !== undefined) { opts.max = max }
    return chance.integer(opts)
}

export function randomFloat(min, max) {
    const opts = {}
    if (min !== undefined) { opts.min = min }
    if (max !== undefined) { opts.max = max }
    return chance.floating(opts)
}

export function randomBool(likelihood) {
    return likelihood ? chance.bool({ likelihood: likelihood }) : chance.bool()
}