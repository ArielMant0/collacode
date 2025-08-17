<template>
    <div class="d-flex align-center justify-center">
        <v-checkbox :model-value="warningsEnabled"
            label="enable warnings"
            color="primary"
            @update:model-value="setWarnings"
            hide-details
            hide-spin-buttons
            density="compact"/>

        <v-checkbox
            label="enable warnings"
            color="primary"
            class="ml-4"
            hide-details
            hide-spin-buttons
            density="compact"/>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { setUserWarnings } from '@/use/data-api';
    import { storeToRefs } from 'pinia';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { warningsEnabled } = storeToRefs(app)

    async function setWarnings(value) {
        try {
            await setUserWarnings(value)
            times.needsReload("users")
        } catch (e) {
            console.error(e.toString())
            toast.error("error updating warning setting")
        }
    }

</script>
