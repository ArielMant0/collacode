<template>
    <div>
        <div>
            <div class="d-flex justify-space-between" style="width: 100%;">
                <v-btn @click="toggleResolveAdd"
                    style="width: 32%;"
                    variant="tonal"
                    color="primary"
                    prepend-icon="mdi-plus">toggle tags to add</v-btn>
                <v-btn @click="reset"
                    style="width: 32%;"
                    variant="tonal">reset</v-btn>
                <v-btn @click="toggleResolveRemove"
                    variant="tonal"
                    color="error"
                    style="width: 32%;"
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
                                <TagText :tag="t"/>
                            </td>
                            <td>
                                <v-icon v-for="(e, idx) in tagEvidence[t.id]" :key="'ev_'+e.id"
                                    :color="app.getUserColor(e.created_by)"
                                    class="cursor-pointer"
                                    @pointerenter="event => hoverEvidence(e, event)"
                                    @pointerleave="hoverEvidence(null)"
                                    @click="clickEvidence(t.id, idx)"
                                    @contextmenu="event => contextEvidence(t.id, idx, event)"
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

        <v-btn
            class="mt-4 mb-1"
            variant="tonal"
            block
            :disabled="!allowEdit || (sumAdd === 0 && sumRemove === 0)"
            @click="submitResolveBoth">
            <span>add <b>{{ sumAdd }}</b> user tags AND remove <b>{{ sumRemove }}</b> user tags</span>
        </v-btn>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { ref, onMounted, computed, watch, reactive } from 'vue';
    import { color, group, pointer } from 'd3';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import { addDataTags, deleteDataTags } from '@/use/data-api';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { useTooltip } from '@/store/tooltip';
import TagText from './TagText.vue';

    const app = useApp()
    const tt = useTooltip()
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

    function hoverEvidence(e, event) {
        if (e) {
            const [mx, my] = pointer(event, document.body)
            tt.showEvidence(e.id, mx, my)
        } else {
            tt.hideEvidence()
        }
    }
    function clickEvidence(tagId, idx) {
        const e = tagEvidence.value[tagId][idx];
        if (e) {
            app.setShowEvidence(e.id, tagEvidence.value[tagId].map(dd => dd.id), idx)
        }
    }

    function contextEvidence(tagId, idx, event) {
        event.preventDefault()
        if (!allowEdit.value) return
        const e = tagEvidence.value[tagId][idx];
        if (e) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "evidence", e.id,
                mx, my,
                null,
                { list: tagEvidence.value[tagId].map(dd => dd.id), index: idx },
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
        tt.hideEvidence()
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
        tt.hideEvidence()
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