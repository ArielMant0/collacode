<template>
    <div style="text-align: center; min-width: 100%;">

        <div class="text-caption">drag similar {{ app.itemName+'s' }} into their fitting category</div>
        <div class="d-flex align-start justify-center" style="min-width: 100%;">
            <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 mr-4" style="max-width: 49%; min-width: 25%; border-radius: 4px;">
                <h3>Suggested Similar {{ app.itemNameCaptial+'s' }}</h3>
                <div class="d-flex flex-wrap justify-center align-start"
                    @drop.prevent="dropItem(0)"
                    @dragover.prevent
                    :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*4)+'px' }">
                    <ItemTeaser v-for="item in restItems"
                        :item="item"
                        :width="imageWidth"
                        :height="imageHeight"
                        prevent-open
                        prevent-context
                        draggable="true"
                        @click="setItem(item.id, 2)"
                        @dragstart="startDrag(item.id)"
                        style="cursor: grab"
                        class="mr-1 mb-1"/>
                </div>
            </div>

            <div class="ml-4" style="max-width: 49%; min-width: 25%;">

                <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 mb-1" style="min-width: 100%; border-radius: 4px;">
                    <h3>Very Similar</h3>
                    <div class="d-flex flex-wrap justify-center align-start"
                        @drop.prevent="dropItem(2)"
                        @dragover.prevent
                        :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*2)+'px' }">
                        <ItemTeaser v-for="item in highItems"
                            :item="item"
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
                    <h3>Somewhat Similar</h3>
                    <div class="d-flex flex-wrap justify-center align-start"
                        @drop.prevent="dropItem(1)"
                        @dragover.prevent
                        :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*2)+'px' }">
                        <ItemTeaser v-for="item in medItems"
                            :item="item"
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
    import { reactive, computed } from 'vue'
    import ItemTeaser from './ItemTeaser.vue'
    import { useDisplay } from 'vuetify'
    import { useToast } from 'vue-toastification'

    const app = useApp()
    const toast = useToast()
    const { md, lg, xl, xxl } = useDisplay()

    const props = defineProps({
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

    const restItems = computed(() => props.items.filter(d => !itemHigh.has(d.id) && !itemMed.has(d.id)))
    const highItems = computed(() => props.items.filter(d => itemHigh.has(d.id)))
    const medItems = computed(() => props.items.filter(d => itemMed.has(d.id)))

    const minW = computed(() => {
        let mul = 1
        if (xxl.value) {
            mul = 5
        } else if (xl.value) {
            mul = 4
        } else if (lg.value) {
            mul = 3
        } else if (md.value) {
            mul = 2
        } else {
            mul = 1
        }
        return Math.min(mul, Math.floor(props.items.length / 4)) * (props.imageWidth+10)
    })

    let dragId = null

    function startDrag(id) {
        dragId = id
    }
    function dropItem(where=0) {
        if (!dragId) return
        setItem(dragId, where)
        dragId = null
    }
    function setItem(id, where=0) {
        if (where === 2) {
            if (props.itemLimit > 0 && itemHigh.size >= props.itemLimit) {
                return toast.warning(`maximum number of ${app.itemName}s reached`)
            }
            itemMed.delete(id)
            itemHigh.add(id)
        } else if (where === 1) {
            if (props.itemLimit > 0 && itemMed.size >= props.itemLimit) {
                return toast.warning(`maximum number of ${app.itemName}s reached`)
            }
            itemHigh.delete(id)
            itemMed.add(id)
        } else {
            itemMed.delete(id)
            itemHigh.delete(id)
        }
        update()
    }

    function resetItem(id) {
        itemHigh.delete(id)
        itemMed.delete(id)
        update()
    }

    function update() {
        emit("update", highItems.value.map(d => ({ id: d.id, value: 2 }))
            .concat(medItems.value.map(d => ({ id: d.id, value: 1 }))))
    }

</script>