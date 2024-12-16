<template>
    <div style="text-align: left;">
        <v-checkbox-btn v-model="deleteChildren"
            density="compact"
            hide-details
            hide-spin-buttons
            label="delete children"/>
        <v-btn color="error" block density="compact" @click="deleteSelected">delete</v-btn>
        <div class="ml-2 text-caption">
            <div v-for="g in grouped" :key="g.id" :title="g.name">
                {{ g.name }}
                <div v-for="t in g.tags" :key="t.id" :title="t.pathNames" class="ml-4">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(t.id)"/>
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
    import { deleteTags, getSubtree } from '@/use/utility';
    import { group } from 'd3';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const deleteChildren = ref(false)
    const grouped = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        const selData = DM.getData("tags", true)
        const g = group(selData, d => d.path[0])
        const arr = []
        g.forEach((tags, parent) => arr.push({ id: parent, name: DM.getDataItem("tags_name", parent), tags: tags }))
        grouped.value = arr;
    }

    async function deleteSelected() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)
        const selData = DM.getData("tags", true)

        if (selData.size > 0) {

            let ids = [];
            if (deleteChildren.value) {
                selData.forEach(d => ids = ids.concat(getSubtree(d, allTags)));
                ids = Array.from(new Set(ids));
            } else {
                ids = selData.map(d => d.id)
            }

            try {
                await deleteTags(ids)
                toast.success("deleted " + ids.length + " tag(s)")
                times.needsReload("tagging")
                resetSelection();
            } catch {
                toast.error("error deleting " + ids.length + " tag(s)")
            }

        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>