import { useApp } from "@/store/app";
import { useLoader } from "./loader"
import { dataPath } from "./utility";
import { autoType, csv } from "d3";

////////////////////////////////////////////////////////////
// Get Data
////////////////////////////////////////////////////////////

export async function loadDatasets() {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("datasets"), autoType)
    }
    const loader = useLoader();
    return loader.get(`datasets`)
}
export async function loadCodesByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("codes", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`codes/dataset/${dataset}`)
}
export async function loadItemsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("items", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`items/dataset/${dataset}`)
}
export async function loadItemsByCode(code) {
    const app = useApp()
    if (app.static) {
        const res = await csv(dataPath("items", app.ds), autoType)
        return res.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`items/code/${code}`)
}
export async function loadItemExpertiseByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("item_expertise", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`item_expertise/dataset/${dataset}`);
}


function kuerzel(str, idx) {
    const split = str.split(new RegExp("[\.\:\-\\s]", "i"))
    if (split.length > 1) {
        return split.slice(0, 3).reduce((acc, s) => acc + s[0], "")
    }
    return str.at(0) + str.at(-1) + (idx+1)
}
export async function loadAllUsers() {
    const app = useApp()
    if (app.static) {
        const list = await csv(dataPath("global_users"), autoType)
        if (app.anonymous) {
            list.forEach(d => d.name = "coder " + d.id)
        }
        list.forEach((d, i) => d.short = kuerzel(d.name, i))
        return list
    }
    const loader = useLoader();
    const list = await loader.get("users");
    if (app.anonymous) {
        list.forEach(d => d.name = "coder " + d.id)
    }
    list.forEach((d, i) => d.short = kuerzel(d.name, i))
    return list
}
export async function loadUsersByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const list = await csv(dataPath("users", dataset), autoType)
        if (app.anonymous) {
            list.forEach(d => d.name = "coder " + d.id)
        }
        list.forEach((d, i) => d.short = kuerzel(d.name, i))
        return list
    }
    const loader = useLoader();
    const list = await loader.get(`users/dataset/${dataset}`)
    if (app.anonymous) {
        list.forEach(d => d.name = "coder " + d.id)
    }
    list.forEach((d, i) => d.short = kuerzel(d.name, i))
    return list
}
export async function loadTagsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("tags", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`tags/dataset/${dataset}`)
}
export async function loadTagsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("tags", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`tags/code/${code}`)
}
export async function loadDataTagsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("datatags", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`datatags/dataset/${dataset}`)
}
export async function loadDataTagsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("datatags", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`datatags/code/${code}`)
}

export async function loadIrrTagsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("irr_tags", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`irr/code/${code}/tags`)
}

export async function loadIrrItemsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("irr_items", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`irr/code/${code}/items`)
}

export async function loadEvidenceByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("evidence", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`evidence/dataset/${dataset}`)
}
export async function loadEvidenceByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("evidence", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`evidence/code/${code}`)
}
export async function loadTagAssignmentsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("tag_assignments", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`tag_assignments/dataset/${dataset}`);
}
export async function loadTagAssignmentsByCodes(oldCode, newCode) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("tag_assignments", app.ds), autoType)
        return resp.filter(d => d.old_code === oldCode && d.new_code === newCode)
    }
    const loader = useLoader();
    return loader.get(`tag_assignments/old/${oldCode}/new/${newCode}`);
}

export async function loadCodeTransitionsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("code_transitions", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`code_transitions/dataset/${dataset}`);
}
export async function loadExtGroupsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("meta_groups", dataset), autoType)
    }
    const loader = useLoader();
    return loader.get(`meta_groups/dataset/${dataset}`);
}
export async function loadExtGroupsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("meta_groups", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`meta_groups/code/${code}`);
}
export async function loadExternalizationsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await csv(dataPath("meta_items", ds), autoType)
    }
    const loader = useLoader();
    return loader.get(`meta_items/dataset/${dataset}`);
}
export async function loadExternalizationsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("meta_items", app.ds), autoType)
        const groups = await loadExtGroupsByCode(code)
        const groupSet = new Set(groups.map(d => d.id))
        return resp.filter(d => groupSet.has(d.group_id))
    }
    const loader = useLoader();
    return loader.get(`meta_items/code/${code}`);
}
export async function loadExtCategoriesByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("meta_categories", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    const loader = useLoader();
    return loader.get(`meta_categories/code/${code}`);
}
export async function loadExtAgreementsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await csv(dataPath("meta_agreements", app.ds), autoType)
        const exts = await loadExternalizationsByCode(code)
        const extSet = new Set(exts.map(d => d.id))
        return resp.filter(d => extSet.has(d.meta_id))
    }
    const loader = useLoader();
    return loader.get(`meta_agreements/code/${code}`);
}
export async function loadExtConnectionsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        return await Promise.all([
            csv(dataPath("meta_cat_connections", dataset), autoType),
            csv(dataPath("meta_tag_connections", dataset), autoType),
            csv(dataPath("meta_ev_connections", dataset), autoType)
        ]);
    }
    const loader = useLoader();
    return Promise.all([
        loader.get(`meta_cat_connections/dataset/${dataset}`),
        loader.get(`meta_tag_connections/dataset/${dataset}`),
        loader.get(`meta_ev_connections/dataset/${dataset}`),
    ])
}
export async function loadExtConnectionsByCode(code) {
    const app = useApp()
    if (app.static) {
        const [resp1, resp2, resp3] = await Promise.all([
            csv(dataPath("meta_cat_connections", app.ds), autoType),
            csv(dataPath("meta_tag_connections", app.ds), autoType),
            csv(dataPath("meta_ev_connections", app.ds), autoType)
        ]);
        const exts = await loadExternalizationsByCode(code)
        const extSet = new Set(exts.map(d => d.id))
        return [
            resp1.filter(d => extSet.has(d.meta_id)),
            resp2.filter(d => extSet.has(d.meta_id)),
            resp3.filter(d => extSet.has(d.meta_id)),
        ]
    }
    const loader = useLoader();
    return Promise.all([
        loader.get(`meta_cat_connections/code/${code}`),
        loader.get(`meta_tag_connections/code/${code}`),
        loader.get(`meta_ev_connections/code/${code}`),
    ])
}
export async function loadObjectionsByCode(code) {
    const app = useApp()
    const loader = useLoader();
    if (app.static) {
        const resp = await csv(dataPath("objections", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    return loader.get(`objections/code/${code}`);
}

export async function loadGameScoresByCode(code) {
    const app = useApp()
    const loader = useLoader();
    if (app.static) {
        const resp = await csv(dataPath("game_scores", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    return loader.get(`game_scores/code/${code}`);
}
export async function loadGameScoresItemsByCode(code) {
    const app = useApp()
    const loader = useLoader();
    if (app.static) {
        const resp = await csv(dataPath("game_scores_items", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    return loader.get(`game_scores_items/code/${code}`);
}
export async function loadGameScoresTagsByCode(code) {
    const app = useApp()
    const loader = useLoader();
    if (app.static) {
        const resp = await csv(dataPath("game_scores_tags", app.ds), autoType)
        return resp.filter(d => d.code_id === code)
    }
    return loader.get(`game_scores_tags/code/${code}`);
}

////////////////////////////////////////////////////////////
// Mini-Game Multiplayer
////////////////////////////////////////////////////////////

export async function loadGameRooms(gameId) {
    const loader = useLoader();
    const app = useApp()
    return loader.get(`lobby/${gameId}/code/${app.currentCode}`);
}
export async function loadRoom(gameId, roomId) {
    const loader = useLoader();
    return loader.get(`lobby/${gameId}/room/${roomId}`);
}
export async function openRoom(gameId, id, name, data=null) {
    const loader = useLoader();
    const app = useApp()
    return loader.post(`lobby/${gameId}/open`, {
        id: id,
        code_id: app.currentCode,
        name: name,
        data: data
    });
}
export async function closeRoom(gameId, id) {
    const loader = useLoader();
    return loader.post(`lobby/${gameId}/close`, { room_id: id });
}
export async function updateRoom(gameId, id) {
    const loader = useLoader();
    return loader.post(`lobby/${gameId}/update`, { room_id: id });
}
export async function joinRoom(gameId, roomId, id, name) {
    const loader = useLoader();
    return loader.post(`lobby/${gameId}/join`, { room_id: roomId, id: id, name: name });
}
export async function leaveRoom(gameId, roomId, id) {
    const loader = useLoader();
    return loader.post(`lobby/${gameId}/leave`, { room_id: roomId, id: id });
}

////////////////////////////////////////////////////////////
// Add/Update/Remove Data
////////////////////////////////////////////////////////////

export async function addDatasets(data) {
    const loader = useLoader();
    return loader.post("add/datasets", { rows: Array.isArray(data) ? data : [data] })
}
export async function updateDatasets(data) {
    const loader = useLoader();
    return loader.post("update/datasets", { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteDatasets(ids) {
    const loader = useLoader();
    return loader.post("delete/datasets", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addUsers(data) {
    const loader = useLoader();
    return loader.post("add/users", { rows: Array.isArray(data) ? data : [data] })
}
export async function updateUsers(data) {
    const loader = useLoader();
    return loader.post("update/users", { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteUsers(ids) {
    const loader = useLoader();
    return loader.post("delete/users", { ids: Array.isArray(ids) ? ids : [ids] })
}
export async function deleteProjectUsers(ids) {
    const loader = useLoader();
    return loader.post("delete/project_users", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addCodes(codes) {
    const app = useApp();
    if (app.ds === null) return;
    const loader = useLoader();
    return loader.post("add/codes", { dataset: app.ds, rows: Array.isArray(codes) ? codes : [codes] })
}
export async function updateCodes(codes) {
    const loader = useLoader();
    return loader.post("update/codes", { rows: Array.isArray(codes) ? codes : [codes] })
}

export async function startCodeTransition(oldCode, newCode) {
    const loader = useLoader();
    return loader.post(`start/code_transition`, { old_code: oldCode, new_code: newCode });
}

export async function addItems(items, dataset, code) {
    const loader = useLoader();
    return loader.post("add/items", { rows: items, dataset: dataset, code: code });
}
export async function deleteItems(ids) {
    const loader = useLoader();
    return loader.post(`delete/items`, { ids: Array.isArray(ids) ? ids : [ids] })

}
export async function updateItems(items) {
    const loader = useLoader();
    return loader.post("update/items", { rows: items });
}
export async function addItemTeaser(name, file, dataset=null) {
    const loader = useLoader();
    const app = useApp()
    dataset = dataset !== null ? dataset : app.ds
    return loader.postImage(`image/teaser/${dataset}/${name}`, file);
}
export async function updateItemTeaser(item, name, file, dataset=null) {
    const loader = useLoader();
    const app = useApp()
    dataset = dataset !== null ? dataset : app.ds
    const resp = await loader.postImage(`image/teaser/${dataset}/${name}`, file);
    item.teaser = resp.name;
    return updateItems([item]);
}
export async function addItemTeasers(data, dataset=null) {
    const loader = useLoader();
    const app = useApp()
    dataset = dataset !== null ? dataset : app.ds
    return loader.postImages(`image/teasers/${dataset}`, data);
}
export async function updateItemTags(item, user, code) {

    const loader = useLoader();
    const body = {
        item_id: item.id,
        user_id: user,
        code_id: code,
        created: Date.now(),
        tags: item.tags.filter(t => t.created_by === user)
    };

    return loader.post("update/item/datatags", body)
}

export async function addTags(obj) {
    const loader = useLoader();
    return loader.post("add/tags", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function updateTags(obj) {
    const loader = useLoader();
    return loader.post("update/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}
export async function deleteTags(ids) {
    const loader = useLoader();
    return loader.post("delete/tags", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function groupTags(parent, obj) {
    const loader = useLoader();
    return loader.post("group/tags", { parent: parent, rows: Array.isArray(obj) ? obj : [obj] })
}
export async function splitTags(obj) {
    const loader = useLoader();
    return loader.post("split/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}
export async function mergeTags(obj) {
    const loader = useLoader();
    return loader.post("merge/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}

export async function addTagAssignments(obj) {
    const loader = useLoader();
    return loader.post("add/tag_assignments", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function updateTagAssignments(obj) {
    const loader = useLoader();
    return loader.post("update/tag_assignments", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function deleteTagAssignments(ids) {
    const loader = useLoader();
    return loader.post("delete/tag_assignments", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addDataTags(data) {
    const loader = useLoader();
    return loader.post("add/datatags", { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteDataTags(ids) {
    const loader = useLoader();
    return loader.post("delete/datatags", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addEvidence(obj) {
    const loader = useLoader();
    return loader.post("add/evidence", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function addEvidenceImage(name, imageData, dataset=null) {
    const loader = useLoader();
    const app = useApp()
    dataset = dataset !== null ? dataset : app.ds
    return loader.postImage(`image/evidence/${dataset}/${name}`, imageData);
}
export async function updateEvidence(obj) {
    const loader = useLoader();
    return loader.post("update/evidence", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function deleteEvidence(ids) {
    const loader = useLoader();
    return loader.post("delete/evidence", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function getSteamFromId(id) {
    const loader = useLoader();
    return loader.get(`import/steam/id/${id}`)
}
export async function getSteamFromName(name) {
    const loader = useLoader();
    return loader.get(`import/steam/name/${name}`)
}

export async function getBookFromISBN(isbn) {
    const loader = useLoader();
    return loader.get(`import/openlibrary/isbn/${isbn}`)
}
export async function getBookFromTitle(name) {
    const loader = useLoader();
    return loader.get(`import/openlibrary/title/${name}`)
}
export async function getBookFromAuthor(name) {
    const loader = useLoader();
    return loader.get(`import/openlibrary/author/${name}`)
}

export async function updateExtGroups(data) {
    const loader = useLoader();
    return loader.post("update/meta_groups", { rows: Array.isArray(data) ? data : [data] })
}

export async function createExternalization(data) {
    const loader = useLoader();
    return loader.post(`add/meta_items`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateExternalization(data) {
    const loader = useLoader();
    return loader.post(`update/meta_items`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExternalization(ids) {
    const loader = useLoader();
    return loader.post("delete/meta_items", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addMetaCatConns(data) {
    const loader = useLoader();
    return loader.post("add/meta_cat_conns", { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteMetaCatConns(ids) {
    const loader = useLoader();
    return loader.post("delete/meta_cat_conns", { ids: Array.isArray(ids) ? ids : [ids] })
}
export async function deleteMetaTagConns(ids) {
    const loader = useLoader();
    return loader.post("delete/meta_tag_conns", { ids: Array.isArray(ids) ? ids : [ids] })
}
export async function deleteMetaEvConns(ids) {
    const loader = useLoader();
    return loader.post("delete/meta_ev_conns", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function createExtCategory(dataset, code, category) {
    const loader = useLoader();
    return loader.post(`add/meta_categories`, {
        dataset: dataset,
        code: code,
        rows: [category]
    })
}
export async function updateExtCategory(data) {
    const loader = useLoader();
    return loader.post(`update/meta_categories`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExtCategories(ids) {
    const loader = useLoader();
    return loader.post(`delete/meta_categories`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addExtAgreement(data) {
    const loader = useLoader();
    return loader.post(`add/meta_agreements`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateExtAgreement(data) {
    const loader = useLoader();
    return loader.post(`update/meta_agreements`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExtAgreement(ids) {
    const loader = useLoader();
    return loader.post(`delete/meta_agreements`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addItemExpertise(data) {
    const loader = useLoader();
    return loader.post(`add/item_expertise`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateItemExpertise(data) {
    const loader = useLoader();
    return loader.post(`update/item_expertise`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteItemExpertise(ids) {
    const loader = useLoader();
    return loader.post(`delete/item_expertise`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addObjections(data) {
    const loader = useLoader();
    return loader.post(`add/objections`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateObjections(data) {
    const loader = useLoader();
    return loader.post(`update/objections`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteObjections(ids) {
    const loader = useLoader();
    return loader.post(`delete/objections`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addGameScores(data) {
    const loader = useLoader();
    return loader.post("add/game_scores", { rows: Array.isArray(data) ? data : [data] })
}
export async function addGameScoresItems(data) {
    const loader = useLoader();
    return loader.post("add/game_scores_items", { rows: Array.isArray(data) ? data : [data] })
}
export async function addGameScoresTags(data) {
    const loader = useLoader();
    return loader.post("add/game_scores_tags", { rows: Array.isArray(data) ? data : [data] })
}

////////////////////////////////////////////////////////////
// Crowd Similarity Data
////////////////////////////////////////////////////////////

export async function getCrowdGUID() {
    const loader = useLoader()
    return loader.get("similarity/guid")
}

export async function postUserCrowdGUID(userId, guid, dataset=null) {
    const app = useApp()
    const loader = useLoader()
    return loader.post("similarity/guid", {
        user_id: userId,
        guid: guid,
        dataset_id: dataset ? dataset : app.ds
    })
}

export async function getSimilarities(dataset=null) {
    const app = useApp()
    const loader = useLoader()
    return loader.get(`similarity/dataset/${dataset ? dataset : app.ds}`)
}

export async function getSimilarByTarget(target, limit=5) {
    const loader = useLoader();
    return loader.get(`similarity/target/${target}/top/${limit}`)
}

export async function addSimilarity(info, data) {
    const loader = useLoader();
    return loader.post("add/similarity", {
        info: info,
        rows: Array.isArray(data) ? data : [data]
    })
}