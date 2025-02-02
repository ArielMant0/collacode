

<template>
    <div v-if="!hidden" class="d-flex flex-column align-center">
        <div class="d-flex">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <MiniTree value-attr="from_id" :value-data="valueData" value-agg="mean"/>
            <span style="width: 100px;" class="ml-2"></span>
        </div>
        <div class="d-flex mb-1">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <TagBarCode ref="allGames" @update="readData"/>
            <span style="width: 100px; text-align: left;" class="text-caption ml-2 pt-1">all {{ app.schemeItemName }}s</span>
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
            <TagBarCode :filter="d => d._selected" :relative="diffSelected" :reference-values="allData"/>
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

    const app = useApp()
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
    const diffSelected = ref(false)

    let loadOnShow = true;

    function readData() {
        if (!props.hidden) {
            loadOnShow = false;
            if (allGames.value) {
                allData.value = allGames.value.getValues()
                const obj = {}
                allData.value.forEach((d, i) => obj[valueDomain.value[i]] = d)
                valueData.value = obj
            } else {
                setTimeout(readData, 150)
            }
        } else {
            loadOnShow = true;
        }
    }
    function readTags() {
        const tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });
        valueDomain.value = tags.map(d => d.id)
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
    watch(() => Math.max(times.tagging, times.tags), read)
</script>