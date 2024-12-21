<template>
    <div class="ml-2 text-caption" style="text-align: left;">
        <div v-for="g in grouped" :key="g.id" :title="g.name">
            {{ g.name }}
            <div v-for="t in g.tags" :key="t.id" :title="t.pathNames" class="ml-4">
                <div class="d-flex align-center">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(t.id)"/>
                    <v-btn
                        icon="mdi-close"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        class="mr-1"
                        density="compact"
                        color="error"
                        @click="app.toggleSelectByTag([t.id])"/>
                    <span>{{ t.name }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { group } from 'd3';
    import { onMounted, watch } from 'vue';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const grouped = ref([])

    function update() {
        const selData = DM.getData("tags", true)
        const g = group(selData, d => d.path[0])
        const arr = []
        g.forEach((tags, parent) => arr.push({ id: parent, name: DM.getDataItem("tags_name", parent), tags: tags }))
        grouped.value = arr;
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>