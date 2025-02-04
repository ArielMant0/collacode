<template>
    <div style="width: 100%;">
        <div ref="el" style="width: 100%;">
            <DynamicTrees v-if="dataOld.length > 0 && dataNew.length > 0 && dataCon.length > 0"
                :highlight-mode="highlightMode"
                :reverse="reverse"
                :max-value="maxValue"
                :width="Math.max(500, width)"
                :clickable-left="interactions"
                :clickable-center="interactions"
                :clickable-right="interactions"
                :code-left="oldCode === app.oldCode ? oldCode : undefined"
                :code-right="newCode === app.newCode ? newCode : undefined"
                @click="onClick"
                @right-click="onRightClick"
                @click-link="onClickLink"
                :draw-left="isActive ? transOld : -1"
                :draw-right="isActive ? transNew : -1"
                :link-mode="linkMode"
                :data-left="dataOld"
                :data-right="dataNew"
                :data-center="dataCon"/>

        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app'
    import { computed, onMounted, ref, watch } from 'vue'
    import DynamicTrees from '@/components/vis/DynamicTrees.vue';
    import DM from '@/use/data-manager';
    import { loadDataTagsByCode, loadTagAssignmentsByCodes, loadTagsByCode, toToTreePath } from '@/use/utility';
    import { sortObjByString } from '@/use/sorting';
    import { useElementSize } from '@vueuse/core';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { FILTER_TYPES } from '@/use/filters';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()
    const { tagAssignMode, transOld, transNew } = storeToRefs(settings)

    const props = defineProps({
        oldCode: {
            type: Number,
            required: true
        },
        newCode: {
            type: Number,
            required: true
        },
        maxValue: {
            type: Number,
            required: false
        },
        highlightMode: {
            type: String,
            default: ""
        },
        linkMode: {
            type: String,
            default: "changes"
        },
        reverse: {
            type: Boolean,
            default: false
        },
        interactions: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["update-max"])

    const el = ref(null)
    const { width } = useElementSize(el)

    const dataOld = ref([])
    const dataNew = ref([])
    const dataCon = ref([])

    const isActive = computed(() => app.oldCode === props.oldCode && app.newCode === props.newCode)

    async function onClick({ data, side }) {
        if (side === "right") {
            app.toggleSelectByTag([data.id])
        } else {
            if (!tagAssignMode.value) tagAssignMode.value = true;
            DM.toggleFilter("tags_old", "id", [data.id], FILTER_TYPES.SET_OR)
        }
    }
    async function onClickLink(data) {
        if (!tagAssignMode.value) tagAssignMode.value = true;
        app.toggleSelectByTag([data.new_tag])
        DM.toggleFilter("tags_old", "id", [data.old_tag], FILTER_TYPES.SET_OR)
    }
    function onRightClick({ data, event }) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag", data.id,
            mx + 15,
            my,
            data.name, null,
            CTXT_OPTIONS.tag
        );
    }

    async function readOld() {
        if (!props.oldCode || !props.newCode) return

        let tags;
        if (props.oldCode === app.oldCode && DM.hasData("tags_old")) {
            tags = DM.getData("tags_old", false).map(d => Object.assign({}, d))
        } else {
            tags = await loadTagsByCode(props.oldCode)
            tags.sort(sortObjByString("name"))
        }

        const  dts = await loadDataTagsByCode(props.oldCode)

        if (tags[0].path === undefined) {
            tags.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, tags);
                t.pathNames = t.path.map(dd => tags.find(tmp => tmp.id === dd).name).join(" / ")
            });
        }

        if (props.oldCode === app.oldCode && !DM.hasData("tags_old")) {
            DM.setData("tags_old", tags)
        }

        const names = new Map(tags.map(d => ([d.id, d.name])))
        // sort tags by hierarchy
        tags.sort((a, b) => {
            if (a.path[0] !== b.path[0]) {
                const pA = names.get(a.path[0])
                const pB = names.get(b.path[0])
                if (pA < pB) return -1;
                if (pA > pB) return  1;
                return 0;
            }
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length - b.path.length
        });

        let maxval = 0;
        tags.forEach(it => {
            const children = new Set(tags.filter(d => d.id !== it.id && d.path.includes(it.id)).map(d => d.id))
            let numDirect = 0, numIndirect = 0;
            dts.forEach(d => {
                if (it.id === d.tag_id) {
                    numDirect++;
                } else if (children.has(d.tag_id)) {
                    numIndirect++;
                }
            })
            it.value = it.path.length
            it.color = numDirect + numIndirect
            maxval = Math.max(numDirect, maxval)
        })
        emit("update-max", maxval)
        dataOld.value = tags;
    }

    async function readNew() {
        if (!props.oldCode || !props.newCode) return

        let tags, dts;
        if (props.newCode === app.newCode && DM.hasData("tags")) {
            tags = DM.getData("tags", false).map(d => Object.assign({}, d))
        } else {
            tags = await loadTagsByCode(props.newCode)
            tags.sort(sortObjByString("name"))
        }

        if (tags[0].path === undefined) {
            tags.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, tags);
                t.pathNames = t.path.map(dd => tags.find(tmp => tmp.id === dd).name).join(" / ")
            });
        }

        if (props.newCode === app.newCode && DM.hasData("datatags")) {
            dts = DM.getData("datatags", false).map(d => Object.assign({}, d))
        } else {
            dts = await loadDataTagsByCode(props.newCode)
        }

        if (props.newCode === app.newCode) {
            if (!DM.hasData("tags")) {
                DM.setData("tags", tags)
            }
            if (!DM.hasData("datatags")) {
                DM.setData("datatags", dts)
            }
        }

        const names = new Map(tags.map(d => ([d.id, d.name])))
        // sort tags by hierarchy
        tags.sort((a, b) => {
            if (a.path[0] !== b.path[0]) {
                const pA = names.get(a.path[0])
                const pB = names.get(b.path[0])
                if (pA < pB) return -1;
                if (pA > pB) return  1;
                return 0;
            }
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });

        let maxval = 0;
        tags.forEach(it => {
            const children = new Set(tags.filter(d => d.id !== it.id && d.path.includes(it.id)).map(d => d.id))
            let numDirect = 0, numIndirect = 0;
            dts.forEach(d => {
                if (it.id === d.tag_id) {
                    numDirect++;
                } else if (children.has(d.tag_id)) {
                    numIndirect++;
                }
            })
            it.value = it.path.length
            it.color = numDirect + numIndirect
            maxval = Math.max(numDirect, maxval)
        })
        emit("update-max", maxval)
        dataNew.value = tags;
    }

    async function readConnections() {
        if (!props.oldCode || !props.newCode ||
            dataOld.value.length === 0 ||
            dataNew.value.length === 0
        ) {
            return
        }

        let array;
        if (props.oldCode === app.oldCode &&
            props.newCode === app.newCode &&
            DM.hasData("tag_assignments")
        ) {
            array = DM.getData("tag_assignments", false)
        } else {
            array = await loadTagAssignmentsByCodes(props.oldCode, props.newCode)
        }

        if (props.oldCode === app.oldCode &&
            props.newCode === app.newCode &&
            !DM.hasData("tag_assignments")) {
            DM.setData("tag_assignments", array)
        }

        const hasChanges = (o, n) => {
            const to = dataOld.value.find(d => d.id === o)
            const tn = dataNew.value.find(d => d.id === n)

            const fromOld = array.filter(d => d.old_tag === o && d.new_tag !== null)
            const toNew = array.filter(d => d.old_tag !== null && d.new_tag === n)

            if (fromOld.length > 1) return "split"
            else if (toNew.length > 1) return "merge"

            if (to.parent < 0 && tn.parent < 0) return "";
            else if (to.parent < 0 || tn.parent < 0) return "move";

            const po = dataOld.value.find(d => d.id === to.parent)
            const pn = dataNew.value.find(d => d.id === tn.parent)

            return array.find(d => d.old_tag === po.id && d.new_tag === pn.id) === undefined ?
                "move" : ""
        }

        const hasLink = new Map()

        dataCon.value = array.map(d => {
            const c = hasChanges(d.old_tag, d.new_tag)
            hasLink.set(d.old_tag, c)
            hasLink.set(d.new_tag, c)
            return {
                id: d.id,
                source: d.old_tag,
                target: d.new_tag,
                changes: c
            }
        })

        dataOld.value.forEach(d => d.changes = hasLink.has(d.id) ? hasLink.get(d.id) : "deleted")
        dataNew.value.forEach(d => d.changes = hasLink.has(d.id) ? hasLink.get(d.id) : "new")
    }

    async function readAll() {
        await Promise.all([readOld(), readNew()])
        return readConnections()
    }

    onMounted(readAll)

    watch(() => Math.max(times.all, times.tags, times.tags_old, times.tagging, times.datatags, times.tag_assignments), function() {
        if (isActive.value) {
            readAll()
        }
    })

    watch(() => props.oldCode, async function() {
        await readOld()
        readConnections()
    })
    watch(() => props.newCode, async function() {
        await readNew()
        readConnections()
    })

</script>
