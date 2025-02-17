
<template>
    <div class="ma-4">
        <CSVImporter v-if="app.datasets.length > 0 && app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { loadDatasets } from '@/use/utility';
    import { onMounted } from 'vue';

    const app = useApp()

    async function loadAllDatasets() {
        try {
            const list = await loadDatasets()
            app.setDatasets(list)
        } catch {
            console.error("could not load datasets")
        }
    }

    onMounted(loadAllDatasets)

</script>
