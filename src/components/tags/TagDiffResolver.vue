<template>
    <div>
        <div>
            <div class="d-flex justify-space-between" style="width: 100%;">
                <v-btn @click="toggleResolveAdd"
                    variant="tonal"
                    class="mr-1"
                    color="primary"
                    prepend-icon="mdi-plus">toggle tags to add</v-btn>
                <v-btn @click="reset" class="mr-1" variant="tonal">reset</v-btn>
                <v-btn @click="toggleResolveRemove"
                    class="mr-1"
                    variant="tonal"
                    color="error"
                    prepend-icon="mdi-delete">toggle tags to remove</v-btn>
            </div>

            <div style="max-height: 70vh; overflow-y: auto;" class="mt-4">
                <table>
                    <thead class="text-subtitle-2">
                        <tr>
                            <th>Tag</th>
                            <th>Evidence</th>
                            <th v-for="c in item.coders" :key="'header_'+c" :style="{ color: app.getUserColor(c) }">
                                <span class="cursor-pointer hover-it" @click="toggleResolveUser(c)">{{ app.getUserName(c) }}</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody class="text-caption">
                        <tr v-for="(t, i) in tags" :class="[i < tags.length-1 && hasDisagreement(t.id) && !hasDisagreement(tags[i+1].id) ? 'botborder' : '', 'onhover']">
                            <td>
                                <span class="cursor-pointer hover-it" @click="toggleResolveTag(t.id)" @contextmenu="e => contextTag(t, e)" :title="t.description">{{ t.name }}</span>
                            </td>
                            <td>
                                <v-icon v-for="e in tagEvidence[t.id]" :key="'ev_'+e.id"
                                    :color="app.getUserColor(e.created_by)"
                                    class="cursor-pointer"
                                    @pointerenter="event => hoverEvidence(e, event)"
                                    @pointerleave="hoverEvidence(null)"
                                    @click="clickEvidence(e)"
                                    @contextmenu="event => contextEvidence(e, event)"
                                    size="xx-small">
                                    mdi-circle</v-icon>
                            </td>
                            <td v-for="user in item.coders" :key="t.id+'_'+user"
                                :style="{ backgroundColor: existing[t.id][user] ? bgColor.get(user) : 'none' }"
                                class="cursor-pointer hoverdark"
                                @click="toggleValue(t.id, user)">
                                <v-icon v-if="matrix[t.id][user]"
                                    density="compact"
                                    size="small"
                                    :color="app.getUserColor(user)">mdi-circle</v-icon>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

        </div>

        <div class="d-flex justify-space-between mt-4">
            <v-btn
                class="text-caption mb-1"
                color="primary"
                variant="tonal"
                style="width: 49%;"
                :disabled="!allowEdit || sumAdd === 0"
                @click="submitResolveAdd"
                density="compact">
                add {{ sumAdd }} user tags
            </v-btn>
            <v-btn
                class="text-caption mb-1"
                color="error"
                variant="tonal"
                style="width: 49%;"
                :disabled="!allowEdit || sumRemove === 0"
                @click="submitResolveRemove"
                density="compact">
                remove {{ sumRemove }} user tags
            </v-btn>
        </div>
        <v-btn
            class="text-caption mb-1"
            variant="tonal"
            block
            :disabled="!allowEdit || (sumAdd === 0 && sumRemove === 0)"
            @click="submitResolveBoth"
            density="compact">
            add {{ sumAdd }} user tags AND remove {{ sumRemove }} user tags
        </v-btn>

        <ToolTip :x="hoverE.x" :y="hoverE.y" :data="hoverE.data">
            <template v-slot:default>
                <EvidenceCell :item="hoverE.data" :height="200" image-fit show-desc/>
            </template>
        </ToolTip>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { ref, onMounted, computed, watch, reactive } from 'vue';
    import { color, group, pointer } from 'd3';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import ToolTip from '../ToolTip.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { addDataTags, deleteDataTags } from '@/use/utility';
    import { ALL_ITEM_OPTIONS, CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        time: {
            type: Number,
            default: 0
        }
    })

    const emit = defineEmits(["submit"])

    const matrix = ref({})
    const existing = ref({})

    const tags = ref([])

    const bgColor = reactive(new Map())
    const hoverE = reactive({
        x: 0, y: 0,
        data: null
    })

    const counts = computed(() => {
        const obj = { add: {}, remove: {} }

        props.item.coders.forEach(u => {
            obj.add[u] = 0
            obj.remove[u] = 0
        })

        if (Object.keys(existing.value).length === 0 ||
            Object.keys(matrix.value).length === 0) return obj

        props.item.coders.forEach(u => {
            props.item.allTags.forEach(t => {
                if (!existing.value[t.id][u] && matrix.value[t.id][u]) {
                    obj.add[u]++
                } else if (existing.value[t.id][u] && !matrix.value[t.id][u]) {
                    obj.remove[u]++
                }
            })
        })

        return obj
    })
    const sumAdd = computed(() => Object.values(counts.value.add).reduce((acc,v) => acc + v, 0))
    const sumRemove = computed(() => Object.values(counts.value.remove).reduce((acc,v) => acc + v, 0))

    const tagEvidence = computed(() => {
        const obj = { time: props.time }

        props.item.evidence.forEach(ev => {
            if (!obj[ev.tag_id]) obj[ev.tag_id] = []
            obj[ev.tag_id].push(ev)
        })

        delete obj.time

        return obj
    })

    function getBgColor(user) {
        const c = color(app.getUserColor(user))
        c.opacity = 0.33
        return c.formatRgb()
    }
    function toggleValue(tag, user) {
        matrix.value[tag][user] = !matrix.value[tag][user]
    }

    function toggleResolveTag(tag) {
        props.item.coders.forEach(u => {
            matrix.value[tag][u] = !matrix.value[tag][u]
        })
    }
    function reset() {
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                matrix.value[t.id][u] = existing.value[t.id][u]
            })
        })
    }
    function toggleResolveAdd() {
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                if (!existing.value[t.id][u]) {
                    matrix.value[t.id][u] = !matrix.value[t.id][u]
                }
            })
        })
    }
    function toggleResolveRemove() {
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                if (existing.value[t.id][u] && hasDisagreement(t.id)) {
                    matrix.value[t.id][u] = !matrix.value[t.id][u]
                }
            })
        })
    }
    function toggleResolveUser(user) {
        props.item.allTags.forEach(t => {
            if (hasDisagreement(t.id)) {
                matrix.value[t.id][user] = !matrix.value[t.id][user]
            }
        })
    }

    async function submitResolveAdd() {
        if (!allowEdit.value) return
        const list = getChangesAdd()
        try {
            await addDataTags(list)
            toast.success(`added ${list.length} user tags`)
            emit("submit", { add: list })
            times.needsReload("datatags")
        } catch (e) {
            console.error(e.toString())
            toast.error(`error adding ${list.length} user tags`)
        }
    }
    async function submitResolveRemove() {
        if (!allowEdit.value) return
        const list = getChangesRemove()
        try {
            await deleteDataTags(list)
            toast.success(`removed ${list.length} user tags`)
            emit("submit", { remove: list })
            times.needsReload("datatags")
        } catch (e) {
            console.error(e.toString())
            toast.error(`error removing ${list.length} user tags`)
        }
    }

    async function submitResolveBoth() {
        if (!allowEdit.value) return
        const data = getChanges()
        try {
            await Promise.all([
                deleteDataTags(data.remove),
                addDataTags(data.add)
            ])
            toast.success(`changed ${data.add.length + data.remove.length} user tags`)
            emit("submit", data)
            times.needsReload("datatags")
        } catch (e) {
            console.error(e.toString())
            toast.error(`error changing ${add.length+remove.length} user tags`)
        }
    }

    function getChanges() {
        const add = [], remove = [];
        const now = Date.now()
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                const ex = existing.value[t.id][u]
                if (ex !== null && !matrix.value[t.id][u]) {
                    remove.push(ex.id)
                } else if (ex === null && matrix.value[t.id][u]) {
                    add.push({
                        item_id: props.item.id,
                        tag_id: t.id,
                        code_id: app.currentCode,
                        created_by: u,
                        created: now
                    })
                }
            })
        })
        return { add: add, remove: remove }
    }
    function getChangesAdd() {
        const add = [];
        const now = Date.now()
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                const ex = existing.value[t.id][u]
                if (ex === null && matrix.value[t.id][u]) {
                    add.push({
                        item_id: props.item.id,
                        tag_id: t.id,
                        code_id: app.currentCode,
                        created_by: u,
                        created: now
                    })
                }
            })
        })
        return add
    }
    function getChangesRemove() {
        const remove = [];
        props.item.allTags.forEach(t => {
            props.item.coders.forEach(u => {
                const ex = existing.value[t.id][u]
                if (ex !== null && !matrix.value[t.id][u]) {
                    remove.push(ex.id)
                }
            })
        })
        return remove
    }

    function hoverEvidence(e, event) {
        if (e) {
            const [mx, my] = pointer(event, document.body)
            hoverE.x = mx + 15;
            hoverE.y = my
            hoverE.data = e
        } else {
            hoverE.data = null
        }
    }
    function clickEvidence(e) {
        app.setShowEvidence(e.id)
    }
    function contextTag(tag, event) {
        event.preventDefault()
        if (!allowEdit.value) return
        if (tag) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "tag", tag.id,
                mx + 15,
                my,
                tag.name, { item: props.item.id },
                ALL_ITEM_OPTIONS
            )
        } else {
            settings.setRightClick(null)
        }
    }
    function contextEvidence(evidence, event) {
        event.preventDefault()
        if (!allowEdit.value) return
        if (evidence) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "evidence", evidence.id,
                mx - 125,
                my,
                null, null,
                CTXT_OPTIONS.evidence
            )
        } else {
            settings.setRightClick(null)
        }
    }

    function hasDisagreement(tag) {
        let count = 0;
        props.item.coders.forEach(u => {
            if (existing.value[tag][u]) {
                count++
            }
        })
        return count !== props.item.coders.length
    }
    function inData(tag, user) {
        return props.item.tags.find(d => d.tag_id === tag && d.created_by === user)
    }

    function read() {
        hoverE.data = null
        const values = {}
        const ex = {}
        bgColor.clear()
        props.item.coders.forEach(u => bgColor.set(u, getBgColor(u)))

        const grouped = group(props.item.tags, d => d.tag_id)
        const t = props.item.allTags.slice()
        t.sort((a, b) => grouped.get(a.id).length - grouped.get(b.id).length)

        // for each tag
        t.forEach(t => {
            values[t.id] = {}
            ex[t.id] = {}
            // for each coder
            props.item.coders.forEach(u => {
                const there = inData(t.id, u)
                // set status to initial status
                values[t.id][u] = there !== undefined
                ex[t.id][u] = there ? there : null
            })
        })

        tags.value = t
        existing.value = ex
        matrix.value = values
    }
    function readUpdate() {
        hoverE.data = null
        props.item.coders.forEach(u => bgColor.set(u, getBgColor(u)))

        const grouped = group(props.item.tags, d => d.tag_id)
        const t = props.item.allTags.slice()
        t.sort((a, b) => grouped.get(a.id).length - grouped.get(b.id).length)

        tags.value = t
        // for each tag
        t.forEach(t => {
            // for each coder
            props.item.coders.forEach(u => {
                const there = inData(t.id, u)
                // set status if not already in the data
                if (existing.value[t.id] === undefined) {
                    existing.value[t.id] = {}
                }
                if (existing.value[t.id][u] === undefined) {
                    existing.value[t.id][u] = there ? there : null
                }
                if (matrix.value[t.id] === undefined) {
                    matrix.value[t.id] = {}
                }
                if (matrix.value[t.id][u] === undefined) {
                    matrix.value[t.id][u] = there !== undefined
                }
            })
        })
    }

    defineExpose({ getChanges })

    onMounted(read)

    watch(() => props.time, readUpdate)
    watch(() => props.item.id, read)
</script>

<style scoped>
.v-theme--customLight .onhover {
    border-bottom: 1px solid white;
}
.v-theme--customLight .onhover:hover {
    border-bottom: 1px solid black;
}
.v-theme--customDark .onhover {
    border-bottom: 1px solid black;
}
.v-theme--customDark .onhover:hover {
    border-bottom: 1px solid white;
}
table {
    text-align: center;
    table-layout: auto;
    border-collapse: collapse;
    width: 100%;
}
td:nth-child(1), th:nth-child(1),
td:nth-child(2), th:nth-child(2) {
    text-align: left;
}
th, td {
    padding: 1px;
    padding-left: 4px;
    padding-right: 4px;
}
.v-theme--customLight .botborder,
.v-theme--customLight .botborder:hover {
    border-bottom: 2px solid black !important;
}
.v-theme--customDark .botborder,
.v-theme--customDark .botborder:hover {
    border-bottom: 2px solid white !important;
}

.hoverdark:hover { filter: brightness(0.75) }
</style>