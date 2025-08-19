<template>
    <AgreementView v-if="activeUserId !== null && hasData" :loading="isLoading"/>
</template>

<script setup>
    import AgreementView from '@/components/views/AgreementView.vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { loadIrrTagsByCode } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { activeUserId, initialized } = storeToRefs(app)
    const { isLoading } = storeToRefs(settings)

    const hasData = ref(false)

    let loadToast = null

    async function loadAgreement() {
        if (!app.currentCode) return
        try {
            loadToast = toast.info("loading agreement..", { timeout: false })
            const irr = await loadIrrTagsByCode(app.currentCode)
            DM.setData("tags_irr", new Map(irr.map(d => ([d.tag_id, d.alpha]))))
        } catch(e) {

            console.error(e.toString())
            toast.error("error loading agreement")
        }
        hasData.value = true
        toast.dismiss(loadToast)
        loadToast = null
        toast.success("loaded agreement!")
    }

    async function init() {
        if (!initialized.value) return
        if (loadToast === null) {
            if (DM.hasData("tags_irr")) {
                hasData.value = true
            } else {
                await loadAgreement()
            }
        }
    }

    onMounted(init)

    watch(() => Math.max(times.tags, times.tagging, times.datatags), loadAgreement)
</script>