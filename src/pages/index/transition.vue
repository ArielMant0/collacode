<template>
    <TransitionView v-if="activeUserId !== null" :loading="isLoading"/>
</template>

<script setup>
    import TransitionView from '@/components/views/TransitionView.vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { onMounted } from 'vue';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { activeUserId } = storeToRefs(app)
    const { isLoading } = storeToRefs(settings)

    onMounted(function() {
        if (!DM.hasData("tags_old")) {
            times.needsReload("tags_old")
        }
        if (!DM.hasData("n_tag_assignments")) {
            times.needsReload("n_tag_assignments")
        }
    })
</script>