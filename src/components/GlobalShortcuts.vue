<template>
    <div>
        <ItemEditor v-model="showGameModel"
            :key="'gie_'+app.showGame"
            :item="app.showGameObj"
            :has-prev="false"
            :has-next="false"
            @cancel="onCancelGame"/>

        <NewTagDialog v-model="addTagModel"
            @cancel="app.setAddTag(null)"
            @submit="app.setAddTag(null)"/>

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
            title="Edit Evidence"
            min-width="600"
            no-actions close-icon>
            <template v-slot:text>
                <EvidenceWidget v-if="app.showEvObj" :item="app.showEvObj" :allowed-tags="app.showEvTags" :allow-edit="allowEdit"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="editTagModel"
            @cancel="app.setEditTag(null)"
            title="Edit Tag"
            min-width="600"
            no-actions close-icon>
            <template v-slot:text>
                <TagWidget
                    :data="app.editTagObj"
                    parents="tags"
                    :can-edit="allowEdit"
                    @cancel="tagEditCancel"
                    @update="tagEditCancel"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtGroupModel"
            @cancel="app.setShowExtGroup(null)"
            title="Edit Externalization Group"
            no-actions close-icon>
            <template v-slot:text>
                <ExternalizationGroupWidget v-if="app.showExtGroupObj"
                    v-model="app.showExtGroupExt"
                    :item="app.showExtGroupObj"
                    :allow-edit="allowEdit"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtModel"
            @cancel="app.setShowExternalization(null)"
            title="Edit Externalization"
            no-actions close-icon>
            <template v-slot:text>
                <ExternalizationWidget v-if="app.showExtObj" :item="app.showExtObj" :allow-edit="allowEdit"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtCatModel"
            @cancel="app.setShowExtCategory(null)"
            title="Edit Externalization Category"
            min-width="350"
            no-actions close-icon>
            <template v-slot:text>
                <ExtCategoryWidget v-if="app.showExtCatObj" :item="app.showExtCatObj" :allow-edit="allowEdit"/>
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

        <MiniDialog v-model="delEvModel"
            @cancel="app.setDeleteEvidence(null)"
            @submit="deleteEv">
            <template v-slot:text>
                <div v-if="app.delEvObj" class="d-flex flex-column align-center">
                    <p>
                        Delete evidence for game
                        <b>{{ DM.getDataItem("games", app.delEvObj.game_id).name }}</b>?
                    </p>
                    <p class="text-caption" style="max-width: 1000px;">{{ app.delEvObj.description }}</p>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="delExtModel"
            @cancel="app.setDeleteExternalization(null)"
            @submit="deleteExt">
            <template v-slot:text>
                <div v-if="app.delExtObj" class="d-flex flex-column align-center">
                    <p class="mb-2">
                        Delete externalization "<b>{{ app.delExtObj.name }}</b>" for the game
                        <b>{{ DM.getDataItem("games", app.delExtObj.game_id).name }}</b>?
                    </p>
                    <p class="text-caption" style="max-width: 1000px;">{{ app.delExtObj.description }}</p>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="delExtCatModel"
            @cancel="app.setDeleteExtCategory(null)"
            @submit="deleteExtCategory">
            <template v-slot:text>
                <div v-if="app.delExtCatObj" class="d-flex flex-column align-center">
                    <p class="mb-2">Delete externliaztion category <b>{{ app.delExtCatObj.name }}</b>?</p>
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
    import { deleteEvidence, deleteExtCategories, deleteExternalization, deleteTags, getSubtree } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import ExtCategoryWidget from './externalization/ExtCategoryWidget.vue';
    import NewExtCategoryDialog from './dialogs/NewExtCategoryDialog.vue';
    import DM from '@/use/data-manager';
    import NewTagDialog from './dialogs/NewTagDialog.vue';
    import ItemEditor from './dialogs/ItemEditor.vue';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const {
        allowEdit,
        showGame,
        editTag, delTag, addTag,
        showEv, addEv, delEv,
        showExtCat, addExtCat, delExtCat,
        showExt, addExt, delExt,
        showExtGroup
    } = storeToRefs(app)

    const showGameModel = ref(showGame.value !== null)

    const addTagModel = ref(addTag.value !== null)
    const editTagModel = ref(editTag.value !== null)
    const delTagModel = ref(delTag.value !== null)

    const showEvModel = ref(showEv.value !== null)
    const addEvModel = ref(addEv.value !== null)
    const delEvModel = ref(delEv.value !== null)

    const showExtModel = ref(showExt.value !== null)
    const addExtModel = ref(addExt.value !== null)
    const delExtModel = ref(delExt.value !== null)

    const showExtCatModel = ref(showExtCat.value !== null)
    const addExtCatModel = ref(addExtCat.value !== null)
    const delExtCatModel = ref(delExtCat.value !== null)

    const showExtGroupModel = ref(showExtGroup.value !== null)

    const deleteChildren = ref(false)

    watch(showGame, () => { if (showGame.value) { showGameModel.value = true } })
    watch(editTag, () => { if (editTag.value) { editTagModel.value = true } })
    watch(showEv, () => { if (showEv.value) { showEvModel.value = true } })
    watch(showExt, () => { if (showExt.value) { showExtModel.value = true } })
    watch(showExtCat, () => { if (showExtCat.value) { showExtCatModel.value = true } })
    watch(showExtGroup, () => { if (showExtGroup.value) { showExtGroupModel.value = true } })

    watch(delTag, () => {
        if (delTag.value) {
            deleteChildren.value = false;
            delTagModel.value = true
        }
    })
    watch(delExtCat, () => {
        if (delExtCat.value) {
            deleteChildren.value = false;
            delExtCatModel.value = true
        }
    })
    watch(delEv, () => { if (delEv.value) { delEvModel.value = true } })
    watch(delExt, () => { if (delExt.value) { delExtModel.value = true } })

    watch(addTag, () => { if (addTag.value !== null) { addTagModel.value = true } })
    watch(addEv, () => { if (addEv.value) { addEvModel.value = true } })
    watch(addExt, () => { if (addExt.value) { addExtModel.value = true } })
    watch(addExtCat, () => { if (addExtCat.value) { addExtCatModel.value = true } })

    function tagEditCancel() {
        editTagModel.value = false;
        app.setEditTag(null)
    }
    function onCancelGame(changes) {
        if (changes) {
            toast.warning("discarding changes ..")
        }
        app.setShowGame(null)
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
                toast.error(`error deleting ${ids.length} tag(s)`)
            }
        }
    }
    async function deleteEv() {
        if (delEv.value !== null) {
            try {
                await deleteEvidence(delEv.value)
                toast.success(`deleted evidence`)
                times.needsReload("evidence")
                app.setDeleteEvidence(null);
            } catch {
                toast.error(`error deleting evidence`)
            }
        }
    }
    async function deleteExt() {
        if (delExt.value !== null) {
            try {
                await deleteExternalization(delExt.value)
                toast.success(`deleted externalization`)
                times.needsReload("externalizations")
                app.setDeleteExternalization(null);
            } catch {
                toast.error(`error deleting externalization`)
            }
        }
    }
    async function deleteExtCategory() {
        if (delExtCat.value !== null) {
            try {
                const ids = deleteChildren.value ? getSubtree(app.delExtCatObj, "ext_categories") : [delExtCat.value]
                await deleteExtCategories(ids)
                toast.success(`deleted ${ids.length} categories`)
                times.needsReload("ext_categories")
                times.needsReload("externalizations")
                app.setDeleteExtCategory(null);
            } catch {
                toast.error(`error deleting ${ids.length} categories`)
            }
        }
    }
</script>