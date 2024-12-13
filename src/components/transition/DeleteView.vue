<template>
    <div style="text-align: left;">
        tags to delete:
        <div class="ml-2">
            <div v-for="s in selData" :key="s.id" :title="s.pathNames" @click="settings.moveToTag(s.id)"><b>{{ s.name }}</b></div>
        </div>
        <v-checkbox-btn v-model="deleteChildren"
            density="compact"
            hide-details
            hide-spin-buttons
            label="delete children"/>
        <v-btn color="error" block density="compact">delete</v-btn>
    </div>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { deleteTags, getSubtree } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(settings)

    const deleteChildren = ref(false)
    const selData = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        selData.value = DM.getData("tags", true)
    }

    async function deleteSelected() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)

        if (selData.value.size > 0) {

            let ids = [];
            if (deleteChildren.value) {
                selData.value.forEach(d => ids = ids.concat(getSubtree(d, allTags)));
                ids = Array.from(new Set(ids));
            } else {
                ids = selData.value.map(d => d.id)
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