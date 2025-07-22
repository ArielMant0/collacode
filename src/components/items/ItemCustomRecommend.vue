<template>
    <div style="text-align: center; min-width: 100%;">

        <div class="text-caption">drag similar {{ app.itemName+'s' }} into their fitting category</div>
        <div class="d-flex align-start justify-center" style="min-width: 100%;">

            <div class="d-flex flex-column mr-4" style="max-width: 49%; min-width: 35%;">

            <div class="bordered-grey-light-thin pa-2 mt-1" style="width: 100%; border-radius: 4px;">
                <h3 class="sectitle bordered-secondary">{{ app.itemNameCaptial }}s with similar names</h3>

                <div class="d-flex flex-wrap justify-center align-start"
                    @drop.prevent="e => dropItem(e, 0)"
                    @dragover.prevent
                    :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*2)+'px' }">
                    <ItemTeaser v-for="(item, idx) in suggs.byName"
                        :id="item.id"
                        :width="imageWidth"
                        :height="imageHeight"
                        prevent-open
                        prevent-context
                        draggable="true"
                        @click="setItem(item.id, 'name', idx, 2)"
                        @dragstart="startDrag(item.id, 'name', idx)"
                        style="cursor: grab"
                        class="mr-1 mb-1"/>
                </div>
            </div>

            <div class="bordered-grey-light-thin pa-2 mt-1" style="width: 100%; border-radius: 4px;">
                <h3 class="sectitle bordered-secondary">Additional {{ app.itemName }}s others picked</h3>
                <div class="d-flex flex-wrap justify-center align-start"
                    @drop.prevent="e => dropItem(e, 0)"
                    @dragover.prevent
                    :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*2)+'px' }">
                    <ItemTeaser v-for="(item, idx) in suggs.byCrowd"
                        :id="item.id"
                        :width="imageWidth"
                        :height="imageHeight"
                        prevent-open
                        prevent-context
                        draggable="true"
                        @click="setItem(item.id, 'crowd', idx, 2)"
                        @dragstart="startDrag(item.id, 'crowd', idx)"
                        style="cursor: grab"
                        class="mr-1 mb-1"/>
                </div>
            </div>

            <div class="bordered-grey-light-thin pa-2 mt-1" style="width: 100%; border-radius: 4px;">

                <v-text-field v-model="search"
                    label="Search for items by name.."
                    prepend-inner-icon="mdi-magnify"
                    color="secondary"
                    variant="outlined"
                    density="compact"
                    class="mb-1"
                    style="width: 100%;"
                    @update:model-value="searchByName"
                    clearable
                    hide-details
                    single-line/>
                <div class="d-flex flex-wrap justify-center align-start"
                    @drop.prevent="e => dropItem(e, 0)"
                    @dragover.prevent
                    @dragenter="onDragEnter"
                    @dragleave="onDragLeave"
                    :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*2)+'px' }">
                    <ItemTeaser v-for="(item, idx) in bySearch"
                        :id="item.id"
                        :width="imageWidth"
                        :height="imageHeight"
                        prevent-open
                        prevent-context
                        draggable="true"
                        @click="setItem(item.id, 'search', idx, 2)"
                        @dragstart="startDrag(item.id, 'search', idx)"
                        style="cursor: grab"
                        class="mr-1 mb-1"/>
                </div>
            </div>
            </div>

            <div class="ml-4" style="max-width: 49%; min-width: 35%;">

                <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 mb-1" style="min-width: 100%; border-radius: 4px;">
                    <h3 class="d-flex align-center">
                        <v-tooltip location="top center">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" class="mr-1" size="sm">mdi-information-outline</v-icon>
                            </template>
                            <template #default>
                                <div>
                                    <div>select {{ app.itemName }}s <b>similar</b> to the target</div>
                                    <p class="mt-1">
                                        there should only be small differences, but the majority
                                        of the core game loop should be the same
                                    </p>
                                </div>
                            </template>
                        </v-tooltip>
                        Very Similar
                        <span v-if="itemLimit > 0" class="ml-1 text-caption">(max. {{ itemLimit }})</span>
                    </h3>
                    <div class="d-flex flex-wrap justify-center align-start pa-2"
                        @drop.prevent="e => dropItem(e, 2)"
                        @dragover.prevent
                        @dragenter="onDragEnter"
                        @dragleave="onDragLeave"
                        :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*3)+'px' }">
                        <ItemTeaser v-for="item in highFixed"
                            :id="item.id"
                            :width="imageWidth"
                            :height="imageHeight"
                            prevent-open
                            prevent-context
                            prevent-click
                            class="mr-1 mb-1"/>
                        <ItemTeaser v-for="item in highItems"
                            :id="item.id"
                            :width="imageWidth"
                            :height="imageHeight"
                            prevent-open
                            prevent-context
                            @click="resetItem(item.id)"
                            draggable="true"
                            @dragstart="startDrag(item.id)"
                            style="cursor: grab"
                            class="mr-1 mb-1"/>
                    </div>
                </div>

                <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 mt-1" style="min-width: 100%; border-radius: 4px;">
                    <h3 class="d-flex align-center">
                        <v-tooltip location="top center">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" class="mr-1" size="sm">mdi-information-outline</v-icon>
                            </template>
                            <template #default>
                                <div>
                                    <div>select {{ app.itemName }}s <b>similar</b> to the target</div>
                                    <p class="mt-1">
                                        there can be some differences (e.g. regarding the setting)
                                        but there should be large overlap regarding the core game loop
                                    </p>
                                </div>
                            </template>
                        </v-tooltip>
                        Similar
                        <span v-if="itemLimit > 0" class="ml-1 text-caption">(max. {{ itemLimit }})</span>
                    </h3>
                    <div class="d-flex flex-wrap justify-center align-start pa-2"
                        @drop.prevent="e => dropItem(e, 1)"
                        @dragover.prevent
                        @dragenter="onDragEnter"
                        @dragleave="onDragLeave"
                        :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*4)+'px' }">
                        <ItemTeaser v-for="item in medFixed"
                            :id="item.id"
                            :width="imageWidth"
                            :height="imageHeight"
                            prevent-open
                            prevent-context
                            prevent-click
                            class="mr-1 mb-1"/>
                        <ItemTeaser v-for="item in medItems"
                            :id="item.id"
                            :width="imageWidth"
                            :height="imageHeight"
                            prevent-open
                            prevent-context
                            @click="resetItem(item.id)"
                            draggable="true"
                            @dragstart="startDrag(item.id)"
                            style="cursor: grab"
                            class="mr-1 mb-1"/>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app'
    import { reactive, computed, onMounted } from 'vue'
    import ItemTeaser from './ItemTeaser.vue'
    import { useDisplay } from 'vuetify'
    import DM from '@/use/data-manager'
    import { getSimilarByTarget } from '@/use/data-api'
    import * as sc from "string-comparison"
    import { useToast } from 'vue-toastification'

    const app = useApp()
    const toast = useToast()
    const { md, lg, xl, xxl } = useDisplay()

    const props = defineProps({
        target: {
            type: Number,
            required: true
        },
        items: {
            type: Array,
            required: true
        },
        imageWidth: {
            type: Number,
            default: 140
        },
        imageHeight: {
            type: Number,
            default: 70
        },
        itemLimit: {
            type: Number,
            default: 0
        }
    })

    const emit = defineEmits(["update"])

    const itemHigh = reactive(new Set())
    const itemMed = reactive(new Set())

    const suggs = reactive({
        byName: [],
        byCrowd: [],
    })
    const search = ref("")
    const bySearch = ref([])

    const chosen = ref([])
    const fixed = reactive(new Set())

    const medFixed = computed(() => props.items.filter(d => d.value === 1))
    const medItems = computed(() => chosen.value.filter(d => itemMed.has(d.id)))
    const highFixed = computed(() => props.items.filter(d => d.value === 2))
    const highItems = computed(() => chosen.value.filter(d => itemHigh.has(d.id)))

    const minW = computed(() => {
        let mul = 1
        if (xxl.value) {
            mul = 6
        } else if (xl.value) {
            mul = 5
        } else if (lg.value) {
            mul = 4
        } else if (md.value) {
            mul = 3
        } else {
            mul = 1
        }
        return mul * (props.imageWidth+10)
    })

    let dragId = null, dragOrigin, dragIndex

    function searchByName() {
        if (search.value && search.value.length > 2) {
            const name = new RegExp(search.value, "gi")
            bySearch.value = DM.getDataBy("items", d => d.allTags.length > 0 && !isChosenItem(d.id) && name.test(d.name))
                .map(d => ({ id: d.id, value: 0 }))
        } else {
            bySearch.value = []
            chosen.value.forEach(d => {
                if (d.origin === "search") {
                    d.origin = null
                }
            })
        }
    }
    async function getSuggestions() {
        const rRep = new RegExp("[_\-]", "gi")
        const rDel = new RegExp("[®©™:\(\)0-9]", "gi")
        const process = name => name.toLowerCase().replaceAll(rRep, " ").replaceAll(rDel, "")
        const names = DM.getDataBy("items", d => isFixedItem(d.id)).map(d => process(d.name))
        const other = DM.getDataBy("items", d => {
            const dn = process(d.name)
            return d.allTags.length > 0 &&
                !isFixedItem(d.id) &&
                (
                    names.some(n => sc.default.jaroWinkler.similarity(n, dn) >= 0.85) ||
                    names.some(n => sc.default.lcs.similarity(n, dn) >= 0.85)
                )
        })
        suggs.byName = other.map(d => ({ id: d.id }))
        const crowd = await getSimilarByTarget(props.target, 20)
        suggs.byCrowd = crowd
            .filter(d => !isFixedItem(d.item_id) && !suggs.byName.find(dd => dd.id === d.item_id))
            .slice(0, 10)
            .map(d => ({ id: d.item_id, value: 0 }))
    }

    function isChosenItem(id) {
        return chosen.value.find(d => d.id === id) || isFixedItem(id)
    }
    function isFixedItem(id) {
        return fixed.has(id) || id === props.target
    }

    function startDrag(id, origin=null, index=-1) {
        dragId = id
        dragOrigin = origin
        dragIndex = index
    }
    function dropItem(event, where=0) {
        if (!dragId) return
        setItem(dragId, dragOrigin, dragIndex, where)
        dragId = null
        dragOrigin = null
        dragIndex = -1
        onDragLeave(event)
    }

    function onDragEnter(event) {
        // color background of drop area on enter
        event.target.classList.add("bg-surface-light")
    }
    function onDragLeave(event) {
        // reset background color of drop area on leave
        event.target.classList.remove("bg-surface-light")
    }

    function addToOrigin(origin, id) {
        if (!origin || id <= 0) return
        switch(origin) {
            case "search":
                bySearch.value.push({ id: id})
                break
            case "name":
                suggs.byName.push({ id: id})
                break
            case "crowd":
                suggs.byCrowd.push({ id: id})
                break
        }
    }
    function removeFromOrigin(origin, index) {
        if (!origin || index < 0) return
        switch(origin) {
            case "search":
                bySearch.value.splice(index, 1)
                break
            case "name":
                suggs.byName.splice(index, 1)
                break
            case "crowd":
                suggs.byCrowd.splice(index, 1)
                break
        }
    }
    function setItem(id, origin, index, where=0) {
        if (where === 2) {
            if (props.itemLimit > 0 && itemHigh.size >= props.itemLimit) {
                return toast.warning(`maximum number of ${app.itemName}s reached`)
            }
            if (!itemMed.has(id) && !itemHigh.has(id)) {
                chosen.value.push({ id: id, origin: origin })
            }
            removeFromOrigin(origin, index)

            itemMed.delete(id)
            itemHigh.add(id)
        } else if (where === 1) {
            if (props.itemLimit > 0 && itemMed.size >= props.itemLimit) {
                return toast.warning(`maximum number of ${app.itemName}s reached`)
            }
            if (!itemMed.has(id) && !itemHigh.has(id)) {
                chosen.value.push({ id: id, origin: origin })
            }
            removeFromOrigin(origin, index)
            itemHigh.delete(id)
            itemMed.add(id)
        } else {
            const idx = chosen.value.findIndex(d => d.id === id)
            let org
            if (idx >= 0) {
                org = chosen.value[idx].origin
                chosen.value.splice(idx, 1)
                if (org) {
                    addToOrigin(org, id)
                }
            }
            itemMed.delete(id)
            itemHigh.delete(id)
        }
        update()
    }

    function resetItem(id) {
        setItem(id, "", -1, 0)
    }

    function update() {
        emit("update", highItems.value.map(d => ({ id: d.id, value: 2, origin: d.origin }))
            .concat(medItems.value.map(d => ({ id: d.id, value: 1, origin: d.origin }))))
    }

    function init() {
        fixed.clear()
        props.items.forEach(d => fixed.add(d.id))
        getSuggestions()
    }

    onMounted(init)

</script>

<style scoped>
.sectitle {
    border-radius: 4px;
    width: 100%;
    padding: 3px 0px;
    vertical-align: middle;
    margin-bottom: 10px;
}
</style>