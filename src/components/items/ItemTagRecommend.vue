<template>
    <div class="d-flex align-start justify-center" style="min-width: 100%;">

        <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 mr-4" style="max-width: 49%; min-width: 25%; border-radius: 4px;">
            <h3>Suggested similar {{ app.itemNameCaptial+'s' }}</h3>
            <div class="d-flex flex-wrap justify-center align-start" :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*4)+'px' }">
                <ItemTeaser v-for="item in restItems"
                    :item="item"
                    @click="toggleCandidate(item.id)"
                    :width="imageWidth"
                    :height="imageHeight"
                    prevent-open
                    prevent-context
                    class="mr-1 mb-1"/>
            </div>
        </div>

        <div class="d-flex flex-column align-center bordered-grey-light-thin pa-2 ml-4" style="max-width: 49%; min-width: 25%; border-radius: 4px;">
            <h3>Your choice of similar {{ app.itemNameCaptial+'s' }}</h3>
            <div class="d-flex flex-wrap justify-center align-start" :style="{ minWidth: minW+'px', width: minW+'px', maxWidth: '100%', minHeight: ((imageHeight+10)*4)+'px' }">
                <ItemTeaser v-for="item in chosenItems"
                    :item="item"
                    @click="toggleCandidate(item.id)"
                    :width="imageWidth"
                    :height="imageHeight"
                    prevent-open
                    prevent-context
                    class="mr-1 mb-1"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app'
    import { reactive, computed } from 'vue'
    import ItemTeaser from './ItemTeaser.vue'
    import { useDisplay } from 'vuetify'

    const app = useApp()
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
    })

    const emit = defineEmits(["update"])

    const itemSel = reactive(new Set())
    const restItems = computed(() => props.items.filter(d => !itemSel.has(d.id)))
    const chosenItems = computed(() => props.items.filter(d => itemSel.has(d.id)))

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

    function toggleCandidate(id) {
        if (itemSel.has(id)) {
            itemSel.delete(id)
        } else {
            itemSel.add(id)
        }
        emit("update", chosenItems.value)
    }

</script>