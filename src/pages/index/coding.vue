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
            @update:model-value="setCrowdFilter"
            hide-details
            hide-spin-buttons
            density="compact"/>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { setUserWarnings } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()
    const settings = useSettings()

    const { warningsEnabled } = storeToRefs(app)
    const { crowdFilter } = storeToRefs(settings)

    function setCrowdFilter(value) {
        if (value) {
            crowdFilter.value = true
            app.selectByItemValue("crowdRobust", "crowdRobust", true)
        } else {
            crowdFilter.value = false
            app.selectByItemValue("crowdRobust", "crowdRobust")
        }
    }

    async function setWarnings(value) {
        try {
            await setUserWarnings(value)
            times.needsReload("users")
        } catch (e) {
            console.error(e.toString())
            toast.error("error updating warning setting")
        }
    }

    onMounted(function() {
        crowdFilter.value = DM.hasFilter("items", "crowdRobust")
    })

    watch(() => times.similarity, function() {
        setCrowdFilter(crowdFilter.value)
    })

</script>
