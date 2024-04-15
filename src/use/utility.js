import DM from "./data-manager";
import { useLoader } from "./loader"
import { format } from "d3";

let count = 0;

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

export function toToTreePath(tag, tags) {
    tags = tags ? tags : DM.getData("tags", false);
    let curr = tag;
    const ids = [];
    while (curr) {
        ids.push(curr.id);
        curr = tags.find(d => d.id === curr.parent);
    }
    return ids.reverse();
}

function getSubtreeRec(node, tree, ids) {
    if (node && tree) {
        ids.push(node.id);
        const children = tree.filter(d => d.parent === node.id);
        children.forEach(c => getSubtreeRec(c, tree, ids))
    }
    return ids
}

export function getSubtree(node, tree) {
    tree = tree ? tree : DM.getData("tags", false);
    const ids = [];
    return getSubtreeRec(node, tree, ids)
}

export function uid(name) {
    return new Id("O-" + (name == null ? "" : name + "-") + ++count);
  }

export class Id {
    constructor(id) {
        this.id = id;
        this.href = new URL(`#${id}`, location) + "";
    }
    toString() {
        return "url(" + this.href + ")";
    }
}

export function formatNumber(number) {
    return format(".2s")(number)
}

