<template>
    <ExploreEvidenceView v-if="activeUserId !== null" :loading="isLoading"/>
</template>

<script setup>
    import ExploreEvidenceView from '@/components/views/ExploreEvidenceView.vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const settings = useSettings()

    const { activeUserId } = storeToRefs(app)
    const { isLoading } = storeToRefs(settings)
</script>