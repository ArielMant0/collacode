<template>
    <div class="d-flex justify-space-between" style="width: 100%;">
        <div class="mr-2">
            Coders
            <div v-for="u in users" :key="u.id" class="d-flex mb-1 align-center">
                <v-chip
                    class="mr-1"
                    :color="u.color"
                    variant="flat"
                    size="small"
                    density="compact">{{ u.id }}</v-chip>
                <v-checkbox-btn
                    :model-value="selected.has(u.id)"
                    :label="u.name"
                    :color="u.color"
                    density="compact"
                    @click="toggleUser(u.id)"
                    class="ml-1"/>
            </div>
        </div>
        <div class="ml-2">
            Tag Inconsistencies
            <div class="d-flex">
                <div style="width: 35px;"></div>
                <MiniTree :node-width="6"/>
            </div>
            <div class="d-flex align-center">
                <div style="width: 35px;">
                    <v-btn
                        density="compact"
                        variant="text"
                        @click="absolute = !absolute"
                        :icon="absolute ? 'mdi-percent-circle-outline' : 'mdi-percent-circle'"/>
                </div>
                <BarCode v-if="tagData.length > 0"
                    :data="tagData"
                    @select="toggleTag"
                    :selected="selectedTagsArray"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="count_inconsistent_rel"
                    abs-value-attr="count_inconsistent"
                    color-scale="interpolateYlOrRd"
                    :show-absolute="absolute"
                    :max-value="absolute ? maxValue : 1"
                    :min-value="0"
                    :width="6"
                    :highlightSize="2"
                    :height="20"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { group } from 'd3';

    const app = useApp()
    const times = useTimes()

    const { users } = storeToRefs(app)

    const selected = reactive(new Set())
    const selectedTags = reactive(new Set())
    const selectedTagsArray = computed(() => Array.from(selectedTags.values()))

    const tagData = ref([])
    const maxValue = ref(1)
    const absolute = ref(false)

    const inCount = new Map();

    let tags;

    function toggleUser(id) {
        if (selected.has(id)) {
            selected.delete(id)
        } else {
            selected.add(id)
        }
        recalculate()
    }
    function toggleTag(tag) {
        if (selectedTags.has(tag.id)) {
            selectedTags.delete(tag.id)
        } else {
            selectedTags.add(tag.id)
        }
        app.toggleSelectById(tag.inconsistent)
    }

    function recalculate() {
        inCount.clear()
        const items = DM.getDataBy("items", d => d.numCoders > 1)

        items.forEach(item => {
            const grouped = group(item.tags, d => d["tag_id"])
            grouped.forEach((dts, tagId) => {
                if (dts.length < item.numCoders && dts.some(d => selected.has(d.created_by))) {
                    if (inCount.has(tagId)) {
                        const obj = inCount.get(tagId)
                        obj.items.push(item.id)
                        obj.value++
                    } else {
                        inCount.set(tagId, {
                            items: [item.id],
                            value: 1
                        })
                    }
                }
            });
        })

        const array = []
        maxValue.value = 1

        tags.forEach(t => {
            if (t.is_leaf === 0) return
            const obj = Object.assign({}, t)
            obj.count = DM.getDataItem("tags_counts", t.id)
            obj.count_inconsistent = 0
            obj.count_inconsistent_rel = 0
            obj.inconsistent = []
            if (inCount.has(t.id)) {
                const other = inCount.get(t.id)
                obj.inconsistent = other.items
                obj.count_inconsistent = other.value
                obj.count_inconsistent_rel = other.value / obj.count
            }
            maxValue.value = Math.max(maxValue.value, obj.count)
            array.push(obj)
        })

        tagData.value = array;
    }

    function init() {
        selected.clear()
        users.value.forEach(d => selected.add(d.id))

        // get tags and sort by hierarchy
        tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });

        const items = DM.getDataBy("items", d => d.numCoders > 1)

        items.forEach(item => {
            const grouped = group(item.tags, d => d["tag_id"])
            grouped.forEach((dts, tagId) => {
                if (dts.length < item.numCoders && dts.some(d => selected.has(d.created_by))) {
                    if (inCount.has(tagId)) {
                        const obj = inCount.get(tagId)
                        obj.items.push(item.id)
                        obj.value++
                    } else {
                        inCount.set(tagId, {
                            items: [item.id],
                            value: 1
                        })
                    }
                }
            });
        })

        const array = []
        maxValue.value = 1

        tags.forEach(t => {
            const obj = Object.assign({}, t)
            obj.count = DM.getDataItem("tags_counts", t.id)
            obj.count_inconsistent = 0
            obj.count_inconsistent_rel = 0
            obj.inconsistent = []
            if (inCount.has(t.id)) {
                const other = inCount.get(t.id)
                obj.inconsistent = other.items
                obj.count_inconsistent = other.value
                obj.count_inconsistent_rel = other.value / obj.count
            }
            maxValue.value = Math.max(maxValue.value, obj.count)
            array.push(obj)
        })

        tagData.value = array;
    }

    onMounted(init)

    watch(() => Math.max(times.all, times.users, times.tagging, times.tags, times.datatags), init)

</script>