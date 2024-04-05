import { useLoader } from "./loader"

export function loadDatasets() {
    const loader = useLoader();
    return loader.get(`datasets`)
}
export function loadCodesByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`codes/dataset/${dataset}`)
}
export function loadGamesByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`games/dataset/${dataset}`)
}
export function loadUsersByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`users/dataset/${dataset}`)
}
export function loadTagsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`tags/dataset/${dataset}`)
}
export function loadTagsByCode(code) {
    const loader = useLoader();
    return loader.get(`tags/code/${code}`)
}
export function loadDataTagsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`datatags/dataset/${dataset}`)
}
export function loadDataTagsByCode(code) {
    const loader = useLoader();
    return loader.get(`datatags/code/${code}`)
}
export function loadEvidenceByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`evidence/dataset/${dataset}`)
}
export function loadEvidenceByCode(code) {
    const loader = useLoader();
    return loader.get(`evidence/code/${code}`)
}
export function loadTagAssignmentsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`tag_assignments/dataset/${dataset}`);
}
export function loadTagAssignmentsByCodes(oldCode, newCode) {
    const loader = useLoader();
    return loader.get(`tag_assignments/old/${oldCode}/new/${newCode}`);
}
export function loadMemosByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`memos/dataset/${dataset}`);
}
export function loadCodeTransitionsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`code_transitions/dataset/${dataset}`);
}