<template>
    <div class="d-flex" style="width: 100%;">
        <div class="mr-8">
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
                <div style="width: 120px;"></div>
                <MiniTree :node-width="6"/>
            </div>
            <div class="d-flex align-center">
                <div style="width: 120px;">
                    <v-btn-toggle v-model="mode" density="compact" mandatory @update:model-value="checkMode" border color="primary">
                        <v-btn rounded="sm" size="small" value="absolute" density="comfortable" variant="plain" icon="mdi-weight"/>
                        <v-btn rounded="sm" size="small" value="absolute_range" density="comfortable" variant="plain" icon="mdi-relative-scale"/>
                        <v-btn rounded="sm" size="small" value="relative" density="comfortable" variant="plain" icon="mdi-percent-circle"/>
                    </v-btn-toggle>
                </div>
                <BarCode v-if="tagData.length > 0"
                    :data="tagData"
                    :domain="domain"
                    @select="toggleTag"
                    :selected="selectedTagsArray"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="count_inconsistent_rel"
                    abs-value-attr="count_inconsistent"
                    :color-scale="colors"
                    :show-absolute="absolute"
                    :max-value="mode === 'absolute' ? globalMaxValue : (mode === 'relative' ? 1 : maxValue)"
                    :min-value="0"
                    :width="6"
                    :highlightSize="2"
                    :height="20"/>
            </div>
            <div class="mt-2">
                <div v-for="([uid, data]) in tagDataPerCoder" :key="uid" class="d-flex align-center">
                    <div v-if="selected.has(+uid)" style="width: 120px;">
                        <v-chip
                            class="mr-1"
                            :color="app.getUserColor(+uid)"
                            variant="flat"
                            size="small"
                            density="compact">{{ uid }}</v-chip>
                    </div>
                    <BarCode v-if="selected.has(+uid)"
                        :data="data"
                        :domain="domain"
                        @select="toggleTag"
                        :selected="selectedTagsArray"
                        selectable
                        id-attr="id"
                        name-attr="name"
                        value-attr="count_inconsistent_rel"
                        abs-value-attr="count_inconsistent"
                        :color-scale="colorPerCoder.get(+uid)"
                        :show-absolute="absolute"
                        :max-value="mode === 'absolute' ? globalMaxValue : (mode === 'relative' ? 1 : maxValue)"
                        :min-value="0"
                        :width="6"
                        :highlightSize="2"
                        :height="20"/>
                </div>
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
    import { group, scaleSequential } from 'd3';
    import { useSettings } from '@/store/settings';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { users } = storeToRefs(app)

    const selected = reactive(new Set())
    const selectedTags = reactive(new Set())
    const selectedTagsArray = computed(() => Array.from(selectedTags.values()))

    const tagData = ref([])
    const colors = ref([])
    const tagDataPerCoder = reactive(new Map())
    const colorPerCoder = reactive(new Map())
    const domain = ref([])

    const globalMaxValue = ref(1)
    const maxValue = ref(1)

    const absolute = ref(false)
    const mode = ref("relative")

    const inCount = new Map();

    let tags;

    function checkMode() {
        switch(mode.value) {
            case "relative":
                absolute.value = false
                break;
            default:
                absolute.value = true;
                break;
        }
    }

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
        app.toggleSelectById(tag.inconsistent.map(d => d.item))
    }
    function readSelected() {
        // TODO:
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
                        obj.found.push({ item: item.id, users: dts.map(d => d.created_by) })
                        obj.value++
                    } else {
                        inCount.set(tagId, {
                            found: [{ item: item.id, users: dts.map(d => d.created_by) }],
                            value: 1
                        })
                    }
                }
            });
        })

        maxValue.value = 1
        globalMaxValue.value = 1
        const array = [], domainArray = []

        const perCoder = {}
        users.value.forEach(u => perCoder[u.id] = {})

        const utc = DM.getData("tags_user_counts", false)

        tags.forEach(t => {
            const obj = {
                id: t.id,
                name: t.name,
                count: DM.getDataItem("tags_counts", t.id),
                count_inconsistent: 0,
                count_inconsistent_rel: 0,
                inconsistent: [],
            }
            domainArray.push(t.id)

            if (inCount.has(t.id)) {
                const other = inCount.get(t.id)
                obj.inconsistent = other.found
                obj.count_inconsistent = other.value
                obj.count_inconsistent_rel = other.value / obj.count

                other.found.forEach(item => item.users.forEach(u => {
                    if (!perCoder[u][t.id]) {
                        perCoder[u][t.id] = {
                            id: t.id,
                            name: t.name,
                            inconsistent: [{ item: item.item }],
                            count: utc.get(t.id).get(u) || 0,
                            count_inconsistent: 1,
                            count_inconsistent_rel: 1,
                        }
                    } else {
                        perCoder[u][t.id].count_inconsistent++
                        perCoder[u][t.id].inconsistent.push({ item: item.item })
                    }
                }))
            }

            maxValue.value = Math.max(maxValue.value, obj.count_inconsistent)
            globalMaxValue.value = Math.max(globalMaxValue.value, obj.count)
            array.push(obj)
        })

        for (const id in perCoder) {
            const list = []
            tags.forEach(t => {
                const obj = perCoder[id][t.id]
                if (obj) {
                    obj.count_inconsistent_rel = obj.count_inconsistent / obj.count
                    maxValue.value = Math.max(maxValue.value, obj.count_inconsistent)
                    list.push(obj)
                }
            })
            tagDataPerCoder.set(id, list)
        }

        domain.value = domainArray
        tagData.value = array;
    }

    function makeColorScales() {
        const start = settings.lightMode ? "white" : "black"
        colors.value = [start, "red"]
        users.value.forEach(d => colorPerCoder.set(d.id, [start, d.color]))
    }

    function init() {
        selected.clear()
        tagData.value = []
        tagDataPerCoder.clear()
        colorPerCoder.clear()

        const start = settings.lightMode ? "white" : "black"
        users.value.forEach(d => {
            selected.add(d.id)
            colorPerCoder.set(d.id, [start, d.color])
        })
        colors.value = [start, "red"]

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

        recalculate()
    }

    onMounted(init)

    watch(() => Math.max(times.all, times.users, times.tagging, times.tags, times.datatags), init)
    watch(() => settings.lightMode, makeColorScales)
    watch(() => times.f_items, readSelected)

</script>