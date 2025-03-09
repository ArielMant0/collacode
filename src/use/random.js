import Chance from "chance"
import DM from "./data-manager"

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

export function randomChoice(array, size=1) {
    return size < 2 ? chance.pickone(array) : chance.pickset(array, size)
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
