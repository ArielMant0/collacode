export const ACTION_TYPE =  Object.freeze({
    ANY: 0,
    ITEM: 1,
    TAG: 2,
    DATATAG: 3,
    EVIDENCE: 4,
    WARNINGS: 5,
    OBJECTION: 6
})

export const ACTION_NAME =  Object.freeze({
    ANY: "any",
    ITEM: "item",
    TAG: "tag",
    DATATAG: "datatag",
    EVIDENCE: "evidence",
    WARNINGS: "warning",
    OBJECTION: "objection"
})

export function parseAction(action) {
    if (action.includes(ACTION_NAME.ITEM)) {
        return ACTION_TYPE.ITEM
    }
    if (action.includes(ACTION_NAME.DATATAG)) {
        return ACTION_TYPE.DATATAG
    }
    if (action.includes(ACTION_NAME.TAG)) {
        return ACTION_TYPE.TAG
    }
    if (action.includes(ACTION_NAME.WARNINGS)) {
        return ACTION_TYPE.WARNINGS
    }
    if (action.includes(ACTION_NAME.EVIDENCE)) {
        return ACTION_TYPE.EVIDENCE
    }
    if (action.includes(ACTION_NAME.OBJECTION)) {
        return ACTION_TYPE.OBJECTION
    }
    return ACTION_TYPE.ANY
}

export function getTagsFromEvidence(data) {
    if (Array.isArray(data)) {
        return data.filter(d => d.tag).map(d => d.tag.id)
    }
    return data.tag ? [data.tag.id] : []
}

export function getItemsFromEvidence(data) {
    if (Array.isArray(data)) {
        return data.filter(d => d.item).map(d => d.item.id)
    }
    return data.item ? [data.item.id] : []
}

export function getTagsFromDatatags(data) {
    if (Array.isArray(data)) {
        return data.map(dd => dd.datatags.filter(d => d.tag).map(d => d.tag.id))
            .filter(d => d.length > 0)
            .flat()
    }

    return data.datatags ? data.datatags.filter(d => d.tag).map(d => d.tag.id) :[]
}

export function getItemsFromDatatags(data) {
    if (Array.isArray(data)) {
        return data.map(d => d.item ? d.item.id : null).filter(d => d !== null)
    }

    return data.item ? [data.item.id] : []
}