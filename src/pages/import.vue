
<template>
    <div class="ma-4">
        <CSVImporter v-if="app.datasets.length > 0 && app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { loadDatasets } from '@/use/utility';
    import { onMounted, watch } from 'vue';

    const app = useApp()
    const times = useTimes()

    async function loadAllDatasets() {
        try {
            const list = await loadDatasets()
            app.setDatasets(list)
        } catch {
            console.error("could not load datasets")
        }
    }

    onMounted(loadAllDatasets)

    watch(() => times.users, function() {
        console.log(app.ds, app.users)
    })

</script>
