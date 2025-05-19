
<template>
    <div class="ma-4">
        <CSVImporter v-if="app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { loadDatasets } from '@/use/data-api';
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
