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