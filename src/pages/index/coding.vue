<template>
    <div class="d-flex align-center justify-center">
        <v-checkbox
            :model-value="warningsEnabled"
            label="enable warnings"
            color="primary"
            @update:model-value="setWarnings"
            hide-details
            hide-spin-buttons
            density="compact"/>

        <v-checkbox
            :model-value="crowdFilter"
            :label="'show only crowd '+app.itemName+'s'"
            color="primary"
            class="ml-4"
            @update:model-value="value => app.setCrowdFilter(value)"
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
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { warningsEnabled, crowdFilter } = storeToRefs(app)

    async function setWarnings(value) {
        try {
            await setUserWarnings(value)
            times.needsReload("users")
        } catch (e) {
            console.error(e.toString())
            toast.error("error updating warning setting")
        }
    }

    function setCrowdFilter() {
        app.setCrowdFilter(crowdFilter.value)
    }

</script>
