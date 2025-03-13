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

        <NewObjectionDialog v-model="addObjModel"
            @cancel="app.setAddObjection(null)"
            @submit="onNewObjection"/>

        <NewEvidenceDialog
            v-model="addEvModel"
            :item="app.addEvObj"
            :tag="app.addEvTag"
            :image="app.addEvImg"
            @cancel="app.setAddEvidence(null)"
            @submit="app.setAddEvidence(null)"/>

        <NewMetaCategoryDialog
            v-model="addExtCatModel"
            @cancel="app.setAddMetaCategory(null)"
            @submit="app.setAddMetaCategory(null)"/>

        <NewMetaItemDialog
            v-model="addExtModel"
            :item="app.addExtObj"
            @cancel="app.setAddMetaItem(null)"
            @submit="app.setAddMetaItem(null)"/>


        <MiniDialog v-model="showEvModel"
            @cancel="app.setShowEvidence(null)"
            title="Edit Evidence"
            min-width="600"
            no-actions close-icon>
            <template v-slot:title>
                <div v-if="app.showEvList">
                    <v-btn icon="mdi-arrow-left"
                        density="compact"
                        rounded="sm"
                        :density="compact"
                        variant="plain"
                        :disabled="app.showEvList < 2"
                        @click="app.setShowEvidence(
                            app.showEvList[app.showEvIdx > 0 ? app.showEvIdx-1 : app.showEvList.length-1],
                            app.showEvList,
                            app.showEvIdx > 0 ? app.showEvIdx-1 : app.showEvList.length-1
                        )"/>
                    <v-btn icon="mdi-arrow-right"
                        rounded="sm"
                        density="compact"
                        class="mr-2"
                        :density="compact"
                        variant="plain"
                        :disabled="app.showEvList < 2"
                        @click="app.setShowEvidence(
                            app.showEvList[app.showEvIdx < app.showEvList.length-1 ? app.showEvIdx+1 : 0],
                            app.showEvList,
                            app.showEvIdx < app.showEvList.length-1 ? app.showEvIdx+1 : 0
                        )"/>
                </div>
                Edit Evidence
            </template>
            <template v-slot:text>
                <EvidenceWidget v-if="app.showEv !== null"
                    :item="app.showEvObj"
                    @remove="app.setShowEvidence(null)"
                    :allowed-tags="app.showEvTags"
                    :allow-edit="allowEdit"/>
            </template>
        </MiniDialog>

        <TagExamples v-if="showTagEx !== null" :id="showTagEx" @close="app.setShowTagExamples(null)"/>

        <MiniDialog v-model="editTagModel"
            @cancel="app.setShowTag(null)"
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

        <MiniDialog v-model="showObjModel"
            @cancel="app.setShowObjection(null)"
            title="Edit Objection"
            no-actions
            close-icon>
            <template v-slot:text>
                <ObjectionWidget
                    :item="app.showObjectionObj"
                    @cancel="app.setShowObjection(null)"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtGroupModel"
            min-width="600"
            @cancel="app.setShowMetaGroup(null)"
            :title="'Edit '+capitalize(app.metaItemName)+' Group'"
            no-actions
            close-icon>
            <template v-slot:text>
                <MetaGroupWidget v-if="app.showExtGroup !== null"
                    v-model="app.showExtGroupExt"
                    :item="app.showExtGroupObj"
                    :allow-edit="allowEdit"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtModel"
            min-width="600"
            @cancel="app.setShowMetaItem(null)"
            :title="'Edit '+capitalize(app.itemName)"
            no-actions
            close-icon>
            <template v-slot:text>
                <MetaItemWidget v-if="app.showExt !== null" :item="app.showExtObj" :allow-edit="allowEdit" @cancel="app.setShowMetaItem(null)"/>
            </template>
        </MiniDialog>

        <MiniDialog v-model="showExtCatModel"
            @cancel="app.setShowMetaCategory(null)"
            title="Edit Meta Category"
            min-width="600"
            no-actions
            close-icon>
            <template v-slot:text>
                <MetaCategoryWidget v-if="app.showExtCat !== null" :item="app.showExtCatObj" :allow-edit="allowEdit"/>
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
                        <b>{{ DM.getDataItem("items", app.delEvObj.item_id).name }}</b>?
                    </p>
                    <p class="text-caption" style="max-width: 1000px;">{{ app.delEvObj.description }}</p>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="delExtModel"
            @cancel="app.setDeleteMetaItem(null)"
            @submit="deleteExt">
            <template v-slot:text>
                <div v-if="app.delExtObj" class="d-flex flex-column align-center">
                    <p class="mb-2">
                        Delete {{ app.metaItemName }} "<b>{{ app.delExtObj.name }}</b>" for the game
                        <b>{{ DM.getDataItem("items", app.delExtObj.item_id).name }}</b>?
                    </p>
                    <p class="text-caption" style="max-width: 1000px;">{{ app.delExtObj.description }}</p>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="delExtCatModel"
            @cancel="app.setDeleteMetaCategory(null)"
            @submit="deleteExtCategory">
            <template v-slot:text>
                <div v-if="app.delExtCatObj" class="d-flex flex-column align-center">
                    <p class="mb-2">Delete meta category <b>{{ app.delExtCatObj.name }}</b>?</p>
                    <v-checkbox-btn v-model="deleteChildren" density="compact" hide-details hide-spin-buttons label="delete children"/>
                </div>
            </template>
        </MiniDialog>

        <Teleport to="body">
            <div v-if="imgEffect.show" :style="{ position: 'absolute', left: imgEffect.x+'px', top: imgEffect.y+'px', zIndex: 2999 }">
                <img :src="imgEffect.src" :width="300"/>
            </div>
        </Teleport>
    </div>
</template>

<script setup>

    import { reactive, ref, watch } from 'vue';
    import { useApp } from '@/store/app';
    import TagWidget from '@/components/tags/TagWidget.vue';
    import MiniDialog from '@/components/dialogs/MiniDialog.vue';
    import NewEvidenceDialog from '@/components/dialogs/NewEvidenceDialog.vue';
    import NewMetaItemDialog from '@/components/dialogs/NewMetaItemDialog.vue';
    import EvidenceWidget from '@/components/evidence/EvidenceWidget.vue';
    import MetaItemWidget from '@/components/meta_items/MetaItemWidget.vue';
    import MetaGroupWidget from './meta_items/MetaGroupWidget.vue';
    import { storeToRefs } from 'pinia';
    import { capitalize, deleteEvidence, deleteExtCategories, deleteExternalization, deleteTags, getSubtree } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import MetaCategoryWidget from './meta_items/MetaCategoryWidget.vue';
    import NewMetaCategoryDialog from './dialogs/NewMetaCategoryDialog.vue';
    import DM from '@/use/data-manager';
    import NewTagDialog from './dialogs/NewTagDialog.vue';
    import ItemEditor from './dialogs/ItemEditor.vue';
    import TagExamples from './tags/TagExamples.vue';
    import ObjectionWidget from './objections/ObjectionWidget.vue';
    import NewObjectionDialog from './dialogs/NewObjectionDialog.vue';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const {
        allowEdit,
        showGame,
        showObjection, addObj,
        editTag, delTag, addTag, showTagEx,
        showEv, addEv, delEv,
        showExtCat, addExtCat, delExtCat,
        showExt, addExt, delExt,
        showExtGroup
    } = storeToRefs(app)

    const imgEffect = reactive({
        show: false,
        src: null,
        x: 0,
        y: 0
    })

    const showGameModel = ref(showGame.value !== null)

    const addTagModel = ref(addTag.value !== null)
    const editTagModel = ref(editTag.value !== null)
    const delTagModel = ref(delTag.value !== null)

    const showEvModel = ref(showEv.value !== null)
    const addEvModel = ref(addEv.value !== null)
    const delEvModel = ref(delEv.value !== null)

    const addObjModel = ref(addObj.value !== null)
    const showObjModel = ref(showObjection.value !== null)

    const showExtModel = ref(showExt.value !== null)
    const addExtModel = ref(addExt.value !== null)
    const delExtModel = ref(delExt.value !== null)

    const showExtCatModel = ref(showExtCat.value !== null)
    const addExtCatModel = ref(addExtCat.value !== null)
    const delExtCatModel = ref(delExtCat.value !== null)

    const showExtGroupModel = ref(showExtGroup.value !== null)

    const deleteChildren = ref(false)

    watch(showGame, () => { if (showGame.value) { showGameModel.value = true } })
    watch(showObjection, () => { if (showObjection.value) { showObjModel.value = true } })
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
    watch(addObj, () => { if (addObj.value !== null) { addObjModel.value = true } })
    watch(addEv, () => { if (addEv.value) { addEvModel.value = true } })
    watch(addExt, () => { if (addExt.value) { addExtModel.value = true } })
    watch(addExtCat, () => { if (addExtCat.value) { addExtCatModel.value = true } })

    watch(() => times.tags, function() {
        if (app.editTag) {
            app.setShowTag(app.editTag)
        }
    })
    watch(() => times.evidence, function() {
        if (app.showEv) {
            app.setShowEvidence(app.showEv)
        }
    })
    watch(() => times.items, function() {
        if (app.showGame) {
            app.setShowItem(app.showGame)
        }
    })
    watch(() => times.meta_items, function() {
        if (app.showExt) {
            app.setShowMetaItem(app.showExt)
        }
    })
    watch(() => times.meta_categories, function() {
        if (app.showExtCat) {
            app.setShowMetaCategory(app.showExtCat)
        }
    })
    watch(() => times.meta_groups, function() {
        if (app.showExtGroup) {
            app.setShowMetaGroup(app.showExtGroup)
        }
    })

    function tagEditCancel() {
        editTagModel.value = false;
        app.setShowTag(null)
    }
    function onCancelGame(changes) {
        if (changes) {
            toast.warning("discarding changes ..")
        }
        app.setShowItem(null)
    }

    function onNewObjection() {
        app.setAddObjection(null)
        imgEffect.x = Math.round(window.innerWidth*0.5) - 150
        imgEffect.y = 25
        imgEffect.src = "images/objection.gif"
        imgEffect.show = true
        setTimeout(() => imgEffect.show = false, 1100)
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
                toast.success(`deleted meta items`)
                times.needsReload("meta_items")
                app.setDeleteMetaItem(null);
            } catch {
                toast.error(`error deleting externalization`)
            }
        }
    }
    async function deleteExtCategory() {
        if (delExtCat.value !== null) {
            try {
                const ids = deleteChildren.value ? getSubtree(app.delExtCatObj, "meta_categories") : [delExtCat.value]
                await deleteExtCategories(ids)
                toast.success(`deleted ${ids.length} categories`)
                times.needsReload("meta_categories")
                times.needsReload("meta_items")
                app.setDeleteMetaCategory(null);
            } catch {
                toast.error(`error deleting ${ids.length} categories`)
            }
        }
    }
</script>