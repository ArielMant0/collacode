<template>
    <div>
        <div v-for="([fkey, fval]) in activeFilters" :key="fkey+'_'+fval.key">
            <div class="d-flex align-start">
                <v-btn
                    class="mr-2"
                    icon="mdi-delete"
                    color="error"
                    size="x-small"
                    density="compact"
                    variant="text"
                    @click="DM.removeFilter(fkey)"/>

                <div class="d-flex justify-space-between" style="width: 100%;">
                    <span>
                        <b>{{ fkey }}</b>: {{ fval.key }} ({{ fval.size }})
                    </span>
                    <div v-if="fval.type === FILTER_TYPES.SET_OR || fval.type === FILTER_TYPES.SET_AND">
                        <v-btn
                            icon="mdi-set-all"
                            size="small"
                            class="mr-1"
                            density="compact"
                            variant="tonal"
                            rounded="sm"
                            :color="fval.type === FILTER_TYPES.SET_OR ? 'primary' : 'default'"
                            @click="convertFilter(fkey, fval, FILTER_TYPES.SET_OR)"/>
                        <v-btn
                            icon="mdi-set-center"
                            size="small"
                            density="compact"
                            variant="tonal"
                            rounded="sm"
                            :color="fval.type === FILTER_TYPES.SET_AND ? 'primary' : 'default'"
                            @click="convertFilter(fkey, fval, FILTER_TYPES.SET_AND)"/>
                    </div>
                    <div v-else-if="fval.type === FILTER_TYPES.RANGE_IN_IN ||
                        fval.type === FILTER_TYPES.RANGE_EX_EX ||
                        fval.type === FILTER_TYPES.RANGE_EX_IN ||
                        fval.type === FILTER_TYPES.RANGE_IN_EX">
                        <v-tooltip text="inclusive + inclusive: [a,b]" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    size="small"
                                    class="text-caption mr-1"
                                    density="compact"
                                    variant="tonal"
                                    rounded="sm"
                                    icon="mdi-numeric-1"
                                    :color="fval.type === FILTER_TYPES.RANGE_IN_IN ? 'primary' : 'default'"
                                    @click="convertFilter(fkey, fval, FILTER_TYPES.RANGE_IN_IN)"/>
                            </template>
                        </v-tooltip>

                        <v-tooltip text="exclusive + exclusive: (a,b)" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    size="small"
                                    class="text-caption mr-1"
                                    density="compact"
                                    variant="tonal"
                                    icon="mdi-numeric-2"
                                    rounded="sm"
                                    :color="fval.type === FILTER_TYPES.RANGE_EX_EX ? 'primary' : 'default'"
                                    @click="convertFilter(fkey, fval, FILTER_TYPES.RANGE_EX_EX)"/>
                            </template>
                        </v-tooltip>

                        <v-tooltip text="exclusive + inclusive: (a,b]" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    size="small"
                                    class="text-caption mr-1"
                                    density="compact"
                                    variant="tonal"
                                    icon="mdi-numeric-3"
                                    rounded="sm"
                                    :color="fval.type === FILTER_TYPES.RANGE_EX_IN ? 'primary' : 'default'"
                                    @click="convertFilter(fkey, fval, FILTER_TYPES.RANGE_EX_IN)"/>
                            </template>
                        </v-tooltip>

                        <v-tooltip text="inclusive + exclusive: [a,b)" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    size="small"
                                    class="text-caption"
                                    density="compact"
                                    variant="tonal"
                                    icon="mdi-numeric-4"
                                    rounded="sm"
                                    :color="fval.type === FILTER_TYPES.RANGE_IN_EX ? 'primary' : 'default'"
                                    @click="convertFilter(fkey, fval, FILTER_TYPES.RANGE_IN_EX)"/>
                            </template>
                        </v-tooltip>
                    </div>
                </div>
            </div>
            <div :style="{
                marginLeft: '10px',
                width: '100%',
                maxWidth: (maxWidth-10)+'px',
                fontSize: 'smaller',
                maxHeight: '100px',
                overflowY: 'auto',
                overflowX: 'hidden'
            }">
                <div v-for="v in fval.asArray()" style="max-width: 100%;">
                    <v-btn
                        class="mr-2"
                        icon="mdi-delete"
                        color="error"
                        size="xx-small"
                        density="compact"
                        variant="text"
                        @click="DM.toggleFilter(fkey, fval.key, [v])"/>

                    <span style="max-width: 100%;" class="text-dots">
                        {{ filterValueName(fkey, fval.key, v) }}
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { FILTER_TYPES, isRangeFilter, isSetFilter } from '@/use/filters';
    import { onMounted, ref, watch } from 'vue';

    const app = useApp()
    const times = useTimes()

    const props = defineProps({
        maxWidth: {
            type: Number,
            default: 300
        }
    })

    const activeFilters = ref([])

    function convertFilter(key, filter, type) {
        if (filter.type !== type) {
            if (isSetFilter(filter.type) && !isSetFilter(type)) return
            if (isRangeFilter(filter.type) && !isRangeFilter(type)) return

            DM.setFilter(
                key,
                filter.key,
                filter.asArray(),
                type,
                filter.attr
            )
        }
    }

    function clip(value) {
        switch (typeof value) {
            case 'string': return value.length > 25 ? value.slice(0, 25)+'..' : value
            case 'number': return value.toFixed(Number.isInteger(value) ? 0 : 2)
            case 'object':
                if (Array.isArray(value)) {
                    return `[${value.map(v => clip(v)).join(', ')}]`
                }
                return JSON.stringify(value)
            default: return value
        }
    }

    function filterValueName(key, attr, value) {
        if (key === "tags" && attr === "id" || attr === "tags") {
            const n = DM.getDataItem("tags_name", value)
            return clip(n ? n : value)
        }
        if (key === "items" && attr === "id" || attr === "item_id") {
            const item = DM.getDataItem("items_id", value)
            return clip(item ? item.name : value)
        }
        if (key === "meta_items" && attr === "id" || attr === "metas") {
            const item = DM.getDataItem("meta_items", value)
            return clip(item ? item.name : value)
        }
        if (key === "meta_categories" && attr === "id" || key === "meta_items" && attr === "categories") {
            const item = DM.getDataItem("meta_categories", value)
            return clip(item ? item.name : value)
        }
        if (key === "users" && attr === "id" || attr === "coders") {
            return app.getUserName(value)
        }
        return clip(value)
    }

    function read() {
        const arr = []
        DM.filters.forEach((map, key) => map.forEach(f => arr.push([key, f])))
        activeFilters.value = arr
    }

    onMounted(read)

    watch(() => times.f_any, read);
</script>