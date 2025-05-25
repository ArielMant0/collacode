

<template>
    <div v-if="!hidden" class="d-flex flex-column align-center">
        <div class="d-flex mb-1">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <MiniTree value-attr="from_id" :value-data="valueData" value-agg="mean" :node-width="nodeSize"/>
            <span style="width: 100px;" class="ml-2"></span>
        </div>
        <div class="d-flex mb-1">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <TagBarCode ref="allGames" :time="time" @update="readData" :node-width="nodeSize"/>
            <span style="width: 100px; text-align: left;" class="text-caption ml-2 pt-1">all {{ app.itemName }}s</span>
        </div>
        <div class="d-flex">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2">
                <v-tooltip text="show difference" location="left" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props"
                            :icon="diffSelected ? 'mdi-minus-circle' : 'mdi-minus-circle-off'"
                            rounded="sm"
                            variant="plain"
                            density="compact"
                            @click="diffSelected = !diffSelected"/>
                    </template>
                </v-tooltip>
            </span>
            <div :style="{ minWidth: (valueDomain.length*nodeSize)+'px' }">
                <TagBarCode ref="selGames" :time="time" filter :relative="diffSelected" :reference-values="allData" :node-width="nodeSize"/>
            </div>
            <span style="width: 100px; text-align: left;" class="text-caption ml-2 pt-1">selection</span>
        </div>
    </div>
</template>

<script setup>
    import { onMounted, watch } from 'vue';
    import TagBarCode from '../tags/TagBarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const { showAllUsers } = storeToRefs(app)
    const times = useTimes()

    const props = defineProps({
        hidden: {
            type: Boolean,
            default: false
        }
    })

    const allData = ref([])
    const valueDomain = ref([])
    const valueData = ref({})

    const allGames = ref(null)
    const selGames = ref(null)

    const diffSelected = ref(false)
    const time = ref(0)

    const nodeSize = computed(() => {
        if (valueDomain.value.length === 0) {
            return 5
        }
        return Math.min(25, Math.max(5, Math.floor(800 / valueDomain.value.length)))
    })

    let loadOnShow = true;

    function readData() {
        if (!props.hidden) {
            loadOnShow = false;
            if (allGames.value) {
                allData.value = allGames.value.getValues()
                const obj = {}
                allData.value.forEach((d, i) => obj[valueDomain.value[i]] = d)
                valueData.value = obj
                if (selGames.value) {
                    selGames.value.makeData()
                }
            }
        } else {
            loadOnShow = true;
        }
    }
    function readTags() {
        valueDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
    }
    function read() {
        readTags()
        readData()
    }

    onMounted(read)

    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            readData()
        }
    })
    watch(() => Math.max(times.all, times.tagging, times.tags), read)
    watch(() => times.datatags, readData)
    watch(() => showAllUsers, readData)
</script>