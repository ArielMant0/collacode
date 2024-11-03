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
            :image="app.addEvImg"
            @cancel="app.setAddEvidence(null)"
            @submit="app.setAddEvidence(null)"/>

        <NewExtCategoryDialog
            v-model="addExtCatModel"
            @cancel="app.setAddExtCategory(null)"
            @submit="app.setAddExtCategory(null)"/>

        <NewExternalizationDialog
            v-model="addExtModel"
            :item="app.addExtObj"
            @cancel="app.setAddExternalization(null)"
            @submit="app.setAddExternalization(null)"/>

        <MiniDialog v-model="showEvModel"
            @cancel="app.setShowEvidence(null)"
            no-actions close-icon>
            <template v-slot:text>
                <EvidenceWidget v-if="app.showEvObj" :item="app.showEvObj" :allowed-tags="app.showEvTags"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtGroupModel"
            @cancel="app.setShowExtGroup(null)"
            title="Externalization Group"
            no-actions close-icon>
            <template v-slot:text>
                <ExternalizationGroupWidget v-if="app.showExtGroupObj"
                    v-model="app.showExtGroupExt"
                    :item="app.showExtGroupObj"
                    :allow-edit="settings.activeTab !== 'coding' || settings.activeTab !== 'transition'"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtModel"
            @cancel="app.setShowExternalization(null)"
            no-actions close-icon>
            <template v-slot:text>
                <ExternalizationWidget v-if="app.showExtObj" :item="app.showExtObj"
                    :allow-edit="settings.activeTab !== 'coding' || settings.activeTab !== 'transition'"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtCatModel"
            @cancel="app.setShowExtCategory(null)"
            no-actions close-icon>
            <template v-slot:text>
                <ExtCategoryWidget v-if="app.showExtCatObj" :item="app.showExtCatObj"
                    :allow-edit="settings.activeTab !== 'coding' || settings.activeTab !== 'transition'"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="delTagModel"
            @cancel="app.setDeleteTag(null)"
            @submit="deleteTag">
            <template v-slot:text>
                <div v-if="app.delTagObj" class="d-flex flex-column align-center">
                    <p class="mb-2">Delete tag <b>{{ app.delTagObj.name }}</b>?</p>
                    <v-checkbox-btn v-model="deleteChildren" density="compact" hide-details hide-spin-buttons label="delete children"/>
                </div>
            </template>
        </MiniDialog>

    </div>
</template>

<script setup>

    import { ref, watch } from 'vue';
    import { useApp } from '@/store/app';
    import TagWidget from '@/components/tags/TagWidget.vue';
    import MiniDialog from '@/components/dialogs/MiniDialog.vue';
    import NewEvidenceDialog from '@/components/dialogs/NewEvidenceDialog.vue';
    import NewExternalizationDialog from '@/components/dialogs/NewExternalizationDialog.vue';
    import EvidenceWidget from '@/components/evidence/EvidenceWidget.vue';
    import ExternalizationWidget from '@/components/externalization/ExternalizationWidget.vue';
    import ExternalizationGroupWidget from './externalization/ExternalizationGroupWidget.vue';
    import { storeToRefs } from 'pinia';
    import { deleteTags, getSubtree } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';
    import ExtCategoryWidget from './externalization/ExtCategoryWidget.vue';
import NewExtCategoryDialog from './dialogs/NewExtCategoryDialog.vue';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()
    const settings = useSettings();

    const {
        editTag, delTag,
        addEv, addExt, addExtCat,
        showEv, showExt, showExtCat, showExtGroup
    } = storeToRefs(app)

    const editTagModel = ref(editTag.value !== null)
    const delTagModel = ref(delTag.value !== null)
    const addEvModel = ref(addEv.value !== null)
    const addExtModel = ref(addExt.value !== null)
    const addExtCatModel = ref(addExtCat.value !== null)
    const showEvModel = ref(showEv.value !== null)
    const showExtModel = ref(showExt.value !== null)
    const showExtCatModel = ref(showExtCat.value !== null)
    const showExtGroupModel = ref(showExtGroup.value !== null)

    const deleteChildren = ref(false)

    watch(editTag, () => { if (editTag.value) { editTagModel.value = true } })
    watch(delTag, () => {
        if (delTag.value) {
            deleteChildren.value = false;
            delTagModel.value = true
        }
    })
    watch(addEv, () => { if (addEv.value) { addEvModel.value = true } })
    watch(addExt, () => { if (addExt.value) { addExtModel.value = true } })
    watch(addExtCat, () => { if (addExtCat.value) { addExtCatModel.value = true } })
    watch(showEv, () => { if (showEv.value) { showEvModel.value = true } })
    watch(showExt, () => { if (showExt.value) { showExtModel.value = true } })
    watch(showExtCat, () => { if (showExtCat.value) { showExtCatModel.value = true } })
    watch(showExtGroup, () => { if (showExtGroup.value) { showExtGroupModel.value = true } })

    function tagEditCancel() {
        editTagModel.value = false;
        app.setEditTag(null)
    }
    async function deleteTag() {
        if (delTag.value !== null) {
            try {
                const ids = deleteChildren.value ? getSubtree(app.delTagObj) : [delTag.value]
                await deleteTags(ids)
                toast.success(`deleted ${ids.length} tag(s)`)
                times.needsReload("tagging")
                app.setDeleteTag(null);
            } catch {
                toast.success(`error deleting ${ids.length} tag(s)`)
            }
        }
    }
</script>