<template>
    <div>

        <MiniDialog v-model="editTagModel" no-actions min-width="500">
            <template v-slot:text>
                <TagWidget
                    :data="app.editTagObj"
                    parents="tags"
                    can-edit
                    can-cancel
                    @cancel="tagEditCancel"
                    @update="tagEditCancel"/>
            </template>
        </MiniDialog>

        <NewEvidenceDialog
            v-model="addEvModel"
            :item="app.addEvObj"
            :tag="app.addEvTag"
            @cancel="app.setAddEvidence(null)"
            @submit="app.setAddEvidence(null)"/>

        <NewExternalizationDialog
            v-model="addExtModel"
            :item="app.addExtObj"
            @cancel="app.setAddExternalization(null)"
            @submit="app.setAddExternalization(null)"/>

        <MiniDialog v-model="showEvModel"
            @cancel="app.setShowEvidence(null)"
            no-actions
            close-icon
            min-width="1400">
            <template v-slot:text>
                <EvidenceWidget v-if="app.showEvObj" :item="app.showEvObj" :allowed-tags="app.showEvTags"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtModel"
            @cancel="app.setShowExternalization(null)"
            min-width="1400"
            no-actions
            close-icon>
            <template v-slot:text>
                <ExternalizationWidget v-if="app.showExtObj" :item="app.showExtObj" :allow-edit="activeTab !== 'exploration'"/>
            </template>
        </MiniDialog>

        <ContextMenu/>
    </div>
</template>

<script setup>

    import { ref, watch } from 'vue';
    import { useApp } from '@/store/app';
    import TagWidget from '@/components/tags/TagWidget.vue';
    import MiniDialog from '@/components/dialogs/MiniDialog.vue';
    import NewEvidenceDialog from '@/components/dialogs/NewEvidenceDialog.vue';
    import ContextMenu from '@/components/dialogs/ContextMenu.vue';
    import NewExternalizationDialog from '@/components/dialogs/NewExternalizationDialog.vue';
    import EvidenceWidget from '@/components/evidence/EvidenceWidget.vue';
    import ExternalizationWidget from '@/components/externalization/ExternalizationWidget.vue';
    import { storeToRefs } from 'pinia';

    const app = useApp()

    const { editTag, addEv, addExt, showEv, showExt } = storeToRefs(app)

    const editTagModel = ref(editTag.value !== null)
    const addEvModel = ref(addEv.value !== null)
    const addExtModel = ref(addExt.value !== null)
    const showEvModel = ref(showEv.value !== null)
    const showExtModel = ref(showExt.value !== null)

    watch(editTag, () => { if (editTag.value) { editTagModel.value = true } })
    watch(addEv, () => { if (addEv.value) { addEvModel.value = true } })
    watch(addExt, () => { if (addExt.value) { addExtModel.value = true } })
    watch(showEv, () => { if (showEv.value) { showEvModel.value = true } })
    watch(showExt, () => { if (showExt.value) { showExtModel.value = true } })

    function tagEditCancel() {
        editTagModel.value = false;
        app.setEditTag(null)
    }
</script>