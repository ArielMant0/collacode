<template>
    <div>
        <div>
            <div class="d-flex justify-space-between" style="width: 100%;">
                <v-btn @click="toggleResolveAdd"
                    style="width: 40%;"
                    variant="tonal"
                    color="primary"
                    :class="{ 'text-caption': !smAndUp }"
                    :prepend-icon="smAndUp ? 'mdi-plus' : null">
                    {{ smAndUp ? 'toggle tags to add' : 'toggle add'  }}
                </v-btn>
                <v-btn @click="reset"
                    :class="{ 'text-caption': !smAndUp }"
                    style="width: 18%;"
                    variant="tonal">reset</v-btn>
                <v-btn @click="toggleResolveRemove"
                    variant="tonal"
                    color="error"
                    style="width: 40%;"
                    :class="{ 'text-caption': !smAndUp }"
                    :prepend-icon="smAndUp ? 'mdi-delete' : null">
                    {{ smAndUp ? 'toggle tags to remove' : 'toggle remove' }}
                </v-btn>
            </div>

            <div style="max-height: 65vh; overflow-y: auto;" class="mt-4">
                <table>
                    <thead class="text-subtitle-2">
                        <tr>
                            <th>Tag</th>
                            <th>Evidence</th>
                            <th>Objections</th>
                            <th v-for="c in coders" :key="'header_'+c" :style="{ color: app.getUserColor(c) }">
                                <span class="cursor-pointer hover-it" @click="toggleResolveUser(c)">{{ smAndUp ? app.getUserName(c) : app.getUserShort(c) }}</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody class="text-caption">
                        <tr v-for="(t, i) in tags" :class="{
                                'botborder': hasBorder(t, i),
                                'onhover': smAndUp
                            }">
                            <td :style="{ maxWidth: smAndUp ? '250px' : '100px' }" class="text-dots">
                                <TagText :id="t.id" :item-id="item.id"/>
                            </td>
                            <td>
                                <div class="d-flex flex-wrap">
                                    <EvidenceDot v-for="(e, idx) in tagEvidence[t.id]"
                                        :evidence="e"
                                        size="small"
                                        :list="getEvidenceList(t.id)"
                                        :index="idx"/>
                                </div>
                            </td>
                            <td>
                                <div class="d-flex flex-wrap">
                                    <ObjectionDot v-for="o in tagObjections[t.id]" :objection="o" size="small"/>
                                </div>
                            </td>
                            <td v-for="user in coders" :key="t.id+'_'+user"
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
            :class="{ 'text-caption': !smAndUp }"
            :disabled="!allowEdit || (sumAdd === 0 && sumRemove === 0)"
            @click="submitResolveBoth">
            <span>add <b>{{ sumAdd }}</b> user tags & remove <b>{{ sumRemove }}</b> user tags</span>
        </v-btn>
    </div>
</template>

<script setup>
    import { OBJECTION_ACTIONS, OBJECTION_STATUS, useApp } from '@/store/app';
    import { ref, onMounted, computed, watch, reactive } from 'vue';
    import { color, group } from 'd3';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import { addDataTags, deleteDataTags, updateObjections } from '@/use/data-api';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { useTooltip } from '@/store/tooltip';
    import TagText from './TagText.vue';
    import { useDisplay } from 'vuetify';
    import EvidenceDot from '../evidence/EvidenceDot.vue';
    import ObjectionDot from '../objections/ObjectionDot.vue';
    import DM from '@/use/data-manager.js';

    const app = useApp()
    const tt = useTooltip()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)
    const { smAndUp } = useDisplay()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        users: {
            type: Array,
            required: false
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

    const coders = computed(() => {
        if (props.users) {
            return props.item.coders.filter(uid => props.users.includes(uid))
        }
        return props.item.coders
    })

    const counts = computed(() => {
        const obj = { add: {}, remove: {} }

        coders.value.forEach(u => {
            obj.add[u] = 0
            obj.remove[u] = 0
        })

        if (Object.keys(existing.value).length === 0 ||
            Object.keys(matrix.value).length === 0) return obj

        coders.value.forEach(u => {
            tags.value.forEach(t => {
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
    const tagObjections = computed(() => {
        const obj = { time: props.time }

        DM.getDataBy("objections", o => {
            if (o.item_id !== props.item.id) return
            if (!obj[o.tag_id]) obj[o.tag_id] = []
            obj[o.tag_id].push(o)
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
            coders.value.forEach(u => {
                matrix.value[t.id][u] = existing.value[t.id][u]
            })
        })
    }
    function toggleResolveAdd() {
        props.item.allTags.forEach(t => {
            coders.value.forEach(u => {
                if (!existing.value[t.id][u]) {
                    matrix.value[t.id][u] = !matrix.value[t.id][u]
                }
            })
        })
    }
    function toggleResolveRemove() {
        props.item.allTags.forEach(t => {
            coders.value.forEach(u => {
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

            const changeObjs = []

            // mark related objections as resolved
            for (const tid in tagObjections.value) {

                // get all add objections
                const addObjs = tagObjections.value[tid].filter(d => d.action === OBJECTION_ACTIONS.ADD)
                // if there are add objections and the tag was added (for at least 1 user) - resolve
                if (addObjs.length > 0 && data.add.find(d => d.tag_id === +tid)) {
                    addObjs.forEach(o => {
                        o.resolution = "automatically resolved through agreement discussion"
                        o.resolved_by = app.activeUserId
                        o.resolved = Date.now()
                        o.status = OBJECTION_STATUS.CLOSED_APPROVE
                        changeObjs.push(o)
                    })
                }

                // get all remove objections
                const delObjs = tagObjections.value[tid].filter(d => d.action === OBJECTION_ACTIONS.REMOVE)
                if (delObjs.length > 0 && existing.value[tid]) {
                    // get all user tags for this tag
                    const delUserTags = Object.values(existing.value[tid]).filter(d => d !== null).map(d => d.id)
                    // if all user tags have been removed - resolve
                    if (delUserTags.length === data.remove.filter(d => delUserTags.includes(d)).length) {
                        delObjs.forEach(o => {
                            o.resolution = "automatically resolved through agreement discussion"
                            o.resolved_by = app.activeUserId
                            o.resolved = Date.now()
                            o.status = OBJECTION_STATUS.CLOSED_APPROVE
                            changeObjs.push(o)
                        })
                    }
                }
            }

            const proms = [
                deleteDataTags(data.remove),
                addDataTags(data.add)
            ]
            if (changeObjs.length > 0) {
                proms.push(updateObjections(changeObjs))
            }

            await Promise.all(proms)

            toast.success(`changed ${data.add.length + data.remove.length} user tags`)
            if (changeObjs.length > 0) {
                toast.success(`resolved ${changeObjs.length} objections`)
            }
            
            emit("submit", data)
            times.needsReload("datatags")

            if (changeObjs.length > 0) {
                times.needsReload("objections")
            }
        } catch (e) {
            console.error(e.toString())
            toast.error(`error changing ${data.add.length+data.remove.length} user tags`)
        }
    }

    function getChanges() {
        const add = [], remove = [];
        const now = Date.now()
        tags.value.forEach(t => {
            coders.value.forEach(u => {
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

    function getEvidenceList(tagId) {
        return tagEvidence.value[tagId].map(dd => dd.id)
    }

    function hasBorder(tag, index) {
        return index < tags.value.length-1 &&
            ((!hasUserTags(tag.id) && hasUserTags(tags.value[index+1].id)) ||
            (hasDisagreement(tag.id) && !hasDisagreement(tags.value[index+1].id)))
    }

    function hasUserTags(tag) {
        let count = 0;
        coders.value.forEach(u => {
            if (existing.value[tag][u]) {
                count++
            }
        })
        return count > 0
    }

    function hasDisagreement(tag) {
        let count = 0;
        coders.value.forEach(u => {
            if (existing.value[tag][u]) {
                count++
            }
        })
        return count !== coders.value.length
    }
    function inData(tag, user) {
        return props.item.tags.find(d => d.tag_id === tag && d.created_by === user)
    }

    function getTags(values, ex) {
        const grouped = group(props.item.tags.filter(dt => coders.value.includes(dt.created_by)), d => d.tag_id)
        const t = props.item.allTags.filter(d => {
            if (!grouped.has(d.id)) return false
            const tagCoders = grouped.get(d.id).map(dt => dt.created_by)
            return coders.value.some(c => tagCoders.includes(c))
        })
        t.sort((a, b) => grouped.get(a.id).length - grouped.get(b.id).length)

        // for each tag
        t.forEach(t => {
            values[t.id] = {}
            ex[t.id] = {}
            // for each coder
            coders.value.forEach(u => {
                const there = inData(t.id, u)
                // set status to initial status
                values[t.id][u] = there !== undefined
                ex[t.id][u] = there ? there : null
            })
        })

        const additional = []
        // for all add discuss/objections for this item
        DM
            .getDataBy("objections", o => {
                return o.tag_id &&
                    o.status === OBJECTION_STATUS.OPEN &&
                    o.item_id === props.item.id &&
                    t.find(tag => tag.id === o.tag_id) === undefined
            })
            .forEach(o => {
                values[o.tag_id] = {}
                ex[o.tag_id] = {}
                coders.value.forEach(u => {
                    values[o.tag_id][u] = false
                    ex[o.tag_id][u] = null
                })
                additional.push(DM.getDataItem("tags", o.tag_id))
            })

        return additional.length > 0 ? additional.concat(t) : t
    }

    function read() {
        tt.hideEvidence()
        bgColor.clear()
        coders.value.forEach(u => bgColor.set(u, getBgColor(u)))
        
        const values = {}
        const ex = {}
        tags.value = getTags(values, ex)

        existing.value = ex
        matrix.value = values
    }

    defineExpose({ getChanges })

    onMounted(read)

    watch(() => props.time, read)
    watch(() => props.item.id, read)
    watch(() => props.users, read)
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