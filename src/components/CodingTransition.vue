<template>
    <div ref="wrapper" v-if="oldCode && newCode">
        <h3 style="text-align: center;" class="mt-4 mb-4">TRANSITION FROM {{ app.getCodeName(oldCode) }} TO {{ app.getCodeName(newCode) }}</h3>

        <v-sheet class="d-flex justify-center mb-2">
            <v-tooltip text="add children to selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-plus" color="primary" @click="openPrompt"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="group selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-group" color="primary" @click="groupTags"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="add as children to first selected tag" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-graph" color="primary" @click="addAsChildren"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="select all tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-select-all" color="secondary" @click="selectAll"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="deselect tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-select" color="secondary" @click="resetSelection"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="delete selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" icon="mdi-delete" color="error" @click="deleteTags"></v-btn>
                </template>
            </v-tooltip>
        </v-sheet>

        <InteractiveTree v-if="data.tagTreeData"
            :data="data.tagTreeData"
            :width="wrapperSize.width.value"
            @click="onClickTag"/>

        <v-dialog v-model="tagPrompt"
            min-width="200"
            width="auto"
            elevation="8"
            density="compact"
            >
            <v-card>
            <v-card-text>
                <div class="d-flex justify-center text-caption">
                    Add
                    <input v-model="numChildren"
                        style="max-width: 40px; background-color: #eee; text-align: right;"
                        type="number"
                        min="1"
                        step="1"
                        density="compact"
                        class="ml-1 mr-1"/>
                    child(ren) to {{ data.selectedTags.size }} tags?
                </div>
            </v-card-text>

            <v-card-actions>
                <v-btn class="ms-2" color="warning" @click="closePrompt">cancel</v-btn>
                <v-btn class="ms-auto" color="primary" @click="addChildren">okay</v-btn>
            </v-card-actions>
            </v-card>
        </v-dialog>

    </div>
</template>

<script setup>
    import { onMounted, reactive, computed } from 'vue';
    import InteractiveTree from './vis/InteractiveTree.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();

    const wrapper = ref(null);
    const wrapperSize = useElementSize(wrapper);

    const props = defineProps({
        oldCode: {
            type: Number,
            required: true
        },
        newCode: {
            type: Number,
            required: true
        },
    })

    const tagPrompt = ref(false);
    const numChildren = ref(2);

    const mouseXPrompt = ref(0);
    const mouseYPrompt = ref(0);


    const { dataLoading } = storeToRefs(app);

    let actionQueue = [];
    const data = reactive({

        tags: [],

        tagTreeData: null,
        tagAssign: [],

        selectedTags: new Set(),
    });

    const selectedTagsData = computed(() => {
        if (data.selectedTags.size > 0) {
            return data.tags.filter(d => data.selectedTags.has(d.id))
        }
        return [];
    });

    function readData(performActions=false) {
        if (!props.oldCode || !props.newCode ||
            !DM.hasData("tags") || !DM.hasData("datatags") ||
            !DM.hasData("tag_assignments")
        ) {
            return;
        }

        data.tags = DM.getData("tags", false);
        data.tagAssign = DM.getData("tag_assignments");
        data.tags.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
            d.old = data.tagAssign.find(dd => dd.new_tag === d.id) !== undefined
        })

        data.tagTreeData = [{ id: -1, name: "root", parent: null }].concat(data.tags)

        if (DM.hasFilter("tags", "id")) {
            data.selectedTags = new Set(DM.getFilter("tags", "id"));
        }

        if (performActions && actionQueue.length > 0) {
            let action = actionQueue.pop();
            do {
                switch(action.action) {
                    case "group tags":
                        addTagsToGroup(action.values.name, action.values.tags);
                        break;
                }
                action = actionQueue.pop();
            } while (action)
        }
    }

    function onClickTag(tag, event) {

        if (data.selectedTags.has(tag.id)) {
            data.selectedTags.delete(tag.id);
        } else {
            data.selectedTags.add(tag.id);
        }
        if (data.selectedTags.size > 0) {
            const sels = Array.from(data.selectedTags.values());
            DM.setFilter("tags", "id", sels)
            DM.setFilter("games", "tags", tags => tags && tags.some(d => sels.includes(d.tag_id)))
        } else {
            DM.removeFilter("tags", "id")
            DM.removeFilter("games", "tags")
        }
        app.selectionTime = Date.now();
        mouseXPrompt.value = event.pageX + 10;
        mouseYPrompt.value = event.pageY + 10;
    }

    function selectAll() {
        data.selectedTags = new Set(data.tags.map(d => d.id));
        const sels = Array.from(data.selectedTags.values());
        DM.setFilter("tags", "id", sels)
        DM.setFilter("games", "tags", tags => tags && tags.some(d => sels.includes(d.tag_id)))
        app.selectionTime = Date.now();
    }

    function addChildren() {
        const num = Number.parseInt(numChildren.value);
        const rows = [];
        const now = Date.now();

        if (data.selectedTags.size && num > 0) {
            selectedTagsData.value.forEach(tag => {
                const name = tag.name;
                for (let i = 0; i < num; ++i) {
                    rows.push({
                        name: name+" child "+(i+1),
                        description: "",
                        code_id: props.newCode,
                        parent: tag.id,
                        is_leaf: true,
                        created: now,
                        created_by: app.activeUserId
                    })
                }
            })
            loader.post("add/tags", { rows: rows })
                .then(() => {
                    toast.success("added " + rows.length + " children to " + data.selectedTags.size + " tags")
                    resetSelection();
                    app.needsReload("transition")
                })

        }
        tagPrompt.value = false;

    }
    function undoMarkDelete() {
        if (data.selectedTags.size > 0) {
            loader.post("add/tags/transitions", { ids: ids })
                .then(() => {
                    toast.success("added " + ids.length + "tag(s)")
                    app.needsReload("transition")
                })
            resetSelection();
        }
    }
    function deleteTags() {
        if (data.selectedTags.size > 0) {
            const ids = Array.from(data.selectedTags.values())
            loader.post("delete/tags", { ids: ids })
                .then(() => {
                    toast.success("deleted " + ids.length + " tag(s)")
                    app.needsReload("transition")
                })
            resetSelection();
        }
    }
    async function groupTags() {
        if (data.selectedTags.size > 0) {
            const parent = {
                name: "new tag subtree",
                description: "",
                code_id: props.newCode,
                created: Date.now(),
                created_by: app.activeUserId,
                is_leaf: false,
                parent: null
            }
            await loader.post("add/tags", { rows: [parent] });
            actionQueue.push({
                action: "group tags",
                values: {
                    tags: Array.from(data.selectedTags.values()),
                    name: "new tag subtree",
                }
            });

            app.needsReload("transition")

        }
        resetSelection();
    }
    async function addAsChildren() {
        if (data.selectedTags.size > 0) {
            const vals = Array.from(data.selectedTags.values())
            const first = data.tags.find(d => d.id === vals[0]);
            const tags = [];
            vals.forEach((d, i) => {
                if (i === 0) return;
                const t = data.tags.find(dd => dd.id === d)
                tags.push({
                    id: d,
                    name: t.name,
                    description: t.description,
                    parent: first ? first : null,
                    is_leaf: t.is_leaf
                });
            })

            await loader.post("update/tags", { rows: tags });
            resetSelection();

            app.needsReload("transition")
            toast.success("updated " + tags.length + "tag(s)")
        }
    }

    function resetSelection() {
        data.selectedTags.clear();
        DM.removeFilter("tags", "id")
        DM.removeFilter("games", "tags")
        app.selectionTime = Date.now();
    }

    async function addTagsToGroup(name, tags) {
        if (tags.length === 0 || !name) return;

        const parent = data.tags.find(d => d.name === name);
        if (!parent) {
            console.error("cannot find parent for grouping")
            return;
        }

        await loader.post("update/tags", { rows: tags.map(d => {
            const tag = data.tags.find(t => t.id === d);
            return {
                id: d,
                name: tag.name,
                description: tag.description,
                parent: parent.id,
                is_leaf: tag.is_leaf
            }
        })});
        toast.success(`updated ${tags.length} tags`);
        app.needsReload("transition");
    }


    function openPrompt() { tagPrompt.value = true; }
    function closePrompt() { tagPrompt.value = false; }

    onMounted(readData)

    watch(() => ([dataLoading.value._all, dataLoading.value.transition]), function() {
        if (dataLoading.value._all === false && dataLoading.value.transition === false) {
            readData(true);
        }
    }, { deep: true });
    watch(() => ([
        dataLoading.value.codes,
        dataLoading.value.tags,
        dataLoading.value.tag_assignments,
        dataLoading.value.code_transitions,
    ]), function(val) {
        if (val && (val.every(d => d === false) || val[4] === false || val[5] === false)) {
            readData();

        }
    }, { deep: true });

</script>