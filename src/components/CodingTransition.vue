<template>
    <div ref="wrapper" v-if="oldCode && newCode">
        <h3>Transition from {{ app.getCodeName(oldCode) }} to {{ app.getCodeName(newCode) }}</h3>

        <InteractiveTree v-if="data.tagTreeData"
            :data="data.tagTreeData"
            :width="wrapperSize.width.value"
            @click="onClickTag"
            @drag="onDragTag"/>

        <v-card v-if="tagPrompt && data.selectedTag " width="300"
            elevation="8"
            density="compact"
            :style="{ 'left': mouseXPrompt+'px', 'top': mouseYPrompt+'px', 'z-index': 2004 }"
            position="absolute"
            >
            <v-card-text>
                <div v-if="!data.selectedTag.delete" class="mb-4 d-flex align-center justify-space-between text-caption">
                    <div class="mb-1 d-flex flex-wrap">
                        Add
                        <input v-model="numChildren"
                            style="max-width: 40px"
                            density="compact"
                            class="ml-1 mr-1"/>
                        child(ren) to tag <b>{{ data.selectedTag.name }}</b>?
                    </div>
                    <v-btn @click="addChildren" class="ml-2" color="primary" density="comfortable">add</v-btn>
                </div>

                <div v-if="data.selectedTag.old">
                    <div v-if="data.selectedTag.delete" class="d-flex align-center justify-space-between text-caption">
                        <div class="mb-1">
                            Undo delete tag <b>{{ data.selectedTag.name }}</b> mark?
                        </div>
                        <v-btn @click="undoMarkDelete" class="ml-2" color="error" density="comfortable">Undo</v-btn>
                    </div>
                    <div v-else class="d-flex align-center justify-space-between text-caption">
                        <div class="mb-1">
                            Mark tag <b>{{ data.selectedTag.name }}</b> as deleted?
                        </div>
                        <v-btn @click="markTagDeleted" class="ml-2" color="error" density="comfortable">Mark</v-btn>
                    </div>
                </div>

                <div v-else>
                    <div class="d-flex align-center justify-space-between text-caption">
                        <div class="mb-1">
                            Delete tag <b>{{ data.selectedTag.name }}</b>?
                        </div>
                        <v-btn @click="deleteTag" class="ml-2" color="error" density="comfortable">Delete</v-btn>
                    </div>
                </div>
            </v-card-text>

            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="closeTagPrompt">cancel</v-btn>
            </v-card-actions>
        </v-card>

    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { onMounted, reactive } from 'vue';
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
        datatags: new Map(),

        tagsNew: [],
        datatagsNew: new Map(),

        tagTreeData: null,
        tagAssign: [],

        left: [],
        right: [],
        connections: [],

        selectedTag: null,
    });

    function readData() {
        if (!props.oldCode || !props.newCode ||
            !DM.hasData("tags") || !DM.hasData("datatags") ||
            !DM.hasData("tagsNew") || !DM.hasData("datatagsNew") ||
            !DM.hasData("tag_assignments")
        ) {
            return;
        }

        data.tags = DM.getData("tags", false);
        data.tags.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
        })
        data.datatags = d3.group(DM.getData("datatags", false), d => d.tag_id);

        data.tagsNew = DM.getData("tagsNew", false);
        data.tagAssign = DM.getData("tag_assignments");
        data.tagsNew.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
            d.old = data.tagAssign.find(dd => dd.new_tag === d.id) !== undefined
        })
        data.datatagsNew = d3.group(DM.getData("datatags", false), d => d.tag_id);

        data.tagTreeData = [{ id: -1, name: "root", parent: null }].concat(data.tagsNew)

        if (actionQueue.length > 0) {
            let action = actionQueue.pop();
            do {
                switch(action.action) {
                    case "group tags":
                        addTagsToGroup(action.values);
                        break;
                }
                action = actionQueue.pop();
            } while (action)
        }
    }

    function onClickTag(tag, event) {
        if (data.selectedTag && data.selectedTag.id === tag.id) {
            data.selectedTag = null;
            tagPrompt.value = false;
        } else {
            data.selectedTag = tag;
            tagPrompt.value = true;
        }
        mouseXPrompt.value = event.pageX + 10;
        mouseYPrompt.value = event.pageY + 10;
    }
    function onDragTag() {

    }

    function addChildren() {
        const num = Number.parseInt(numChildren.value);
        if (data.selectedTag && num > 0) {
            const rows = [];
            const now = Date.now();
            const name = data.selectedTag.name;
            for (let i = 0; i < num; ++i) {
                rows.push({
                    name: name+" child "+(i+1),
                    description: "",
                    code_id: props.newCode,
                    parent: data.selectedTag.id,
                    is_leaf: true,
                    created: now,
                    created_by: app.activeUserId
                })
            }
            loader.post("add/tags", { rows: rows })
                .then(() => {
                    toast.success("added " + rows.length + " children to " + name)
                    app.needsReload("transition")
                })
        }
        data.selectedTag = null;
        tagPrompt.value = false;

    }
    function undoMarkDelete() {
        if (data.selectedTag && data.selectedTag.old) {
            data.selectedTag.delete = false;
        }
        data.selectedTag = null;
        tagPrompt.value = false;
    }
    function markTagDeleted() {
        if (data.selectedTag && data.selectedTag.old) {
            data.selectedTag.delete = true;
        }
        data.selectedTag = null;
        tagPrompt.value = false;
    }
    function deleteTag() {
        if (data.selectedTag && !data.selectedTag.old) {
            const name = data.selectedTag.name;
            loader.post("delete/tags", { ids: [data.selectedTag.id] })
                .then(() => {
                    toast.success("deleted tag " + name)
                    app.needsReload("transition")
                })
        }
        data.selectedTag = null;
        tagPrompt.value = false;
    }

    function onClickRight(id, event) {
        clickedGroup.value = id;
        groupPrompt.value = true;
        mouseXGroup.value = event.pageX - 210;
        mouseYGroup.value = event.pageY + 10;
    }
    function onClickConnection(from, to, event) {
        const g = data.tagGroups.find(d => d.id === to);
        const gItems = data.codeTrans.get(to)
        if (g && gItems) {
            const tag = data.tags.find(d => d.id === from);
            const t = gItems.find(d => d.tag_id === from);
            if (t && tag) {
                data.clickedTransObj = {
                    tag: tag.name,
                    group: g.name,
                };
                clickedTrans.value = t.id;
                connectionPrompt.value = true;
                mouseXConn.value = event.pageX + 10;
                mouseYConn.value = event.pageY + 10;
            }
        }
    }

    function openGroupingDialog(useExisting) {
        groupingDialog.value = true;
        useExistingGroup.value = useExisting !== undefined ? useExisting : data.tagGroups.length > 0;
    }
    function cancelGrouping() {
        newGroupName.value = "";
        newGroupDesc.value = "";
        chosenGroup.value = "";
        groupingDialog.value = false;
    }
    function submitGrouping() {
        let valid = false;
        if (!useExistingGroup.value && newGroupName.value && newGroupDesc) {
            valid = true;
            loader.post("add/tag_groups", {
                dataset: app.ds,
                old_code: props.oldCode,
                new_code: props.newCode,
                rows: [{ name: newGroupName.value, description: newGroupDesc.value, created: Date.now() }]
            }).then(() => {

                if (data.selectedTags.size > 0) {
                    actionQueue.push({
                        action: "group tags",
                        values: {
                            tags: Array.from(data.selectedTags.values()),
                            name: newGroupName.value
                        }
                    });
                }
                toast.success("added tag group " + newGroupName.value)
                app.needsReload("tag_groups");
                newGroupName.value = "";
                newGroupDesc.value = "";
            })

        } else if (useExistingGroup.value && chosenGroup.value) {
            valid = true;
            addTagsToGroup(Array.from(data.selectedTags.values()), chosenGroup.value)
        }

        if (valid) {
            groupingDialog.value = false;
        } else {
            toast.error("please select or create a tag group")
        }
    }

    async function addTagsToGroup(tags, group) {
        if (tags.length === 0 || !group) return;

        await loader.post("add/code_transitions", { group: group, rows: tags.map(d => ({ tag_id: d })) });
        toast.success(`added ${tags.length} tags to tag group`);
        app.needsReload("code_transitions");
    }

    function closeTagPrompt() {
        tagPrompt.value = false;
        data.selectedTag = null;
    }
    function cancelCodeTransPrompt() {
        connectionPrompt.value = false;
        clickedTrans.value = "";
        data.clickedTransObj = null;
    }

    function actionDeleteTagGroup() {
        if (clickedGroup.value) {
            groupPrompt.value = false;
            loader.post("delete/tag_groups", { ids: [clickedGroup.value] })
                .then(() => {
                    toast.success("deleted 1 tag group")
                    clickedGroup.value = "";
                    app.needsReload("tag_groups");
                    app.needsReload("code_transitions");
                })
        }
    }
    function actionAddTagsToGroup() {
        if (clickedGroup.value && data.selectedTags.size > 0) {
            addTagsToGroup(Array.from(data.selectedTags.values()), clickedGroup.value)
            groupPrompt.value = false;
            clickedGroup.value = "";
        }
    }
    function actionDeleteCodeTrans() {
        if (clickedTrans.value) {
            connectionPrompt.value = false;
            loader.post("delete/code_transitions", { ids: [clickedTrans.value] })
                .then(() => {
                    toast.success("deleted 1 code transition")
                    clickedTrans.value = "";
                    data.clickedTransObj = null;
                    app.needsReload("code_transitions");
                })
        }
    }

    onMounted(readData)

    watch(() => ([dataLoading.value._all, dataLoading.value.transition]), function() {
        if (dataLoading.value._all === false || dataLoading.value.transition === false) {
            readData();
        }
    }, { deep: true });
    watch(() => ([
        dataLoading.value.codes,
        dataLoading.value.tags,
        dataLoading.value.datatags,
        dataLoading.value.tag_groups,
        dataLoading.value.code_transitions,
    ]), function(val) {
        if (val && (!val.some(d => d === true) || val[4] === false || val[5] === false)) {
            readData();
        }
    }, { deep: true });

</script>