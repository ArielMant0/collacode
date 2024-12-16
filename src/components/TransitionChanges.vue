<template>
    <div style="width: 100%;">
        <div ref="el" style="width: 100%;">
            <DynamicTrees v-if="dataOld.length > 0 && dataNew.length > 0 && dataCon.length > 0"
                :highlight="highlight"
                :reverse="reverse"
                :max-value="maxValue"
                :width="Math.max(500, width)"
                :clickable-right="interactions"
                :code-left="oldCode === app.oldCode ? oldCode : undefined"
                :code-right="newCode === app.newCode ? newCode : undefined"
                @click="onClick"
                @right-click="onRightClick"
                :link-mode="linkMode"
                :data-left="dataOld"
                :data-right="dataNew"
                :data-center="dataCon"/>

        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app'
    import { onMounted, ref, watch } from 'vue'
    import DynamicTrees from '@/components/vis/DynamicTrees.vue';
    import DM from '@/use/data-manager';
    import { loadDataTagsByCode, loadTagAssignmentsByCodes, loadTagsByCode, toToTreePath } from '@/use/utility';
    import { sortObjByString } from '@/use/sorting';
    import { useElementSize } from '@vueuse/core';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';

    const app = useApp()
    const settings = useSettings()

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
        highlight: {
            type: Boolean,
            default: false
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

    function onClick({ data, side }) {
        if (side === "right") {
            app.toggleSelectByTag([data.id])
        }
    }
    function onRightClick({ data, event }) {
        settings.setRightClick(
            "tag", data.id,
            event.pageX + 10,
            event.pageY,
            null,
            CTXT_OPTIONS.tag
        );
    }

    async function readOld() {
        if (!props.oldCode || !props.newCode) return

        let tags, dts;
        if (props.oldCode === app.oldCode && DM.hasData("tags_old")) {
            tags = DM.getData("tags_old", false).map(d => Object.assign({}, d))
        } else {
            tags = await loadTagsByCode(props.oldCode)
            tags.sort(sortObjByString("name"))
        }


        if (props.oldCode === app.oldCode && DM.hasData("datatags_old")) {
            dts = DM.getData("datatags_old", false).map(d => Object.assign({}, d))
        } else {
            dts = await loadDataTagsByCode(props.oldCode)
        }

        if (tags[0].path === undefined) {
            tags.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, tags);
                t.pathNames = t.path.map(dd => tags.find(tmp => tmp.id === dd).name).join(" / ")
            });
        }

        if (props.oldCode === app.oldCode) {
            if (!DM.hasData("tags_old")) {
                DM.setData("tags_old", tags)
            }
            if (!DM.hasData("datatags_old")) {
                DM.setData("datatags_old", dts)
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
            return a.path.length - b.path.length
        });

        let maxval = 0;
        tags.forEach(it => {
            const subset = dts.filter(d => it.path.includes(d.tag_id))
            it.value = it.path.length
            it.color = subset.length
            maxval = Math.max(subset.length, maxval)
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

        if (props.oldCode === app.newCode && DM.hasData("datatags")) {
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
            const subset = dts.filter(d => it.path.includes(d.tag_id))
            it.value = it.path.length
            it.color = subset.length
            maxval = Math.max(subset.length, maxval)
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
            if (!o || !n) return false

            const to = dataOld.value.find(d => d.id === o)
            const tn = dataNew.value.find(d => d.id === n)
            if (!to || !tn) return false

            if (to.parent < 0 && tn.parent < 0) return false;
            else if (to.parent < 0 || tn.parent < 0) return true;

            const po = dataOld.value.find(d => d.id === to.parent)
            const pn = dataNew.value.find(d => d.id === tn.parent)

            return array.find(d => d.old_tag === po.id && d.new_tag === pn.id) === undefined
        }

        dataCon.value = array.map(d => ({
            id: d.id,
            source: d.old_tag,
            target: d.new_tag,
            changes: hasChanges(d.old_tag, d.new_tag)
        }))
    }

    async function readAll() {
        await Promise.all([readOld(), readNew()])
        return readConnections()
    }

    onMounted(readAll)

    watch(() => props.oldCode, async function() {
        await readOld()
        readConnections()
    })
    watch(() => props.newCode, async function() {
        await readNew()
        readConnections()
    })

</script>
