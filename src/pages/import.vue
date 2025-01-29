
<template>
    <div class="ma-4">
        <CSVImporter v-if="!isLoading && app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const settings = useSettings()
    const { isLoading } = storeToRefs(settings)
</script>
