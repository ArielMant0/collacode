<template>
    <ToolTip :x="clickX" :y="clickY" :data="clickTargetId" close-on-outside-click @close="close" align="left" :zIndex="3999">
        <template v-slot:default>
            <div ref="el" class="d-flex flex-column text-caption">
                <div v-if="clickLabel !== null">
                    <div>{{ clickLabel }}</div>
                    <v-divider class="mb-1"></v-divider>
                </div>
                <div v-for="(groups, idx) in clickOptions">
                    <v-divider v-if="idx > 0" class="mt-1 mb-1"></v-divider>
                    <div v-for="o in groups" class="cursor-pointer pl-1 pr-1 grey-on-hover" @click="select(o)">
                        <v-icon v-if="o.icon" :icon="o.icon" density="compact" size="small" class="mr-1"/>
                        <span>{{ o.text }}</span>
                    </div>
                </div>
                <div class="mt-2 pl-1 pr-1 cursor-pointer grey-on-hover" @click="close"><i>cancel</i></div>
            </div>
        </template>
    </ToolTip>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { CTXT_IDS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { addDataTags, deleteDataTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { useToast } from 'vue-toastification';
    import ToolTip from '../ToolTip.vue';

    const emit = defineEmits(["select", "cancel"])

    const app = useApp();
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings();

    const {
        clickTarget,
        clickTargetId,
        clickData,
        clickLabel,
        clickX,
        clickY,
        clickOptions
    } = storeToRefs(settings)

    const el = ref(null)

    function getId(target) {
        if (target === clickTarget.value) {
            return clickTargetId.value
        }
        return clickData.value ? clickData.value[target] : null
    }

    function select(option) {
        switch(option.id) {
            case CTXT_IDS.TAG_EDIT:
                app.toggleShowTag(getId("tag"));
                break;
            case CTXT_IDS.TAG_DEL:
                app.toggleDeleteTag(getId("tag"));
                break;
            case CTXT_IDS.TAG_ADD:
                app.toggleAddTag(getId("tag"));
                break;
            case CTXT_IDS.TAG_TOGGLE:
                toggleTagAssignment(getId("item"), getId("tag"))
                break;
            case CTXT_IDS.TAG_EX:
                app.toggleShowTagExamples(getId("tag"))
                break;
            case CTXT_IDS.EV_ADD:
                app.toggleAddEvidence(getId("item"), getId("tag"))
                break;
            case CTXT_IDS.EV_EDIT:
                app.toggleShowEvidence(getId("evidence"), getId("list"), getId("index"))
                break;
            case CTXT_IDS.EV_DEL:
                app.toggleDeleteEvidence(getId("evidence"))
                break;
            case CTXT_IDS.META_ADD:
                app.toggleAddMetaItem(getId("item"), getId("group"), getId("tag"), getId("evidence"))
                break;
            case CTXT_IDS.META_EDIT:
                app.toggleShowMetaItem(getId("meta_item"))
                break;
            case CTXT_IDS.META_DEL:
                app.toggleDeleteMetaItem(getId("meta_item"))
                break;
            case CTXT_IDS.META_CAT_ADD:
                app.toggleAddMetaCategory(getId("meta_category"), getId("parent"))
                break;
            case CTXT_IDS.META_CAT_EDIT:
                app.toggleShowMetaCategory(getId("meta_category"))
                break;
            case CTXT_IDS.META_CAT_DEL:
                app.toggleDeleteMetaCategory(getId("meta_category"))
                break;
            // all other options
            default:
                if (option.callback) {
                    option.callback(clickData.value)
                }
        }
        settings.setRightClick(null)
        emit("select", option);
    }

    function close() {
        settings.setRightClick(null)
        emit("cancel")
    }

    async function toggleTagAssignment(itemId=null, tagId=null) {
        if (app.allowEdit && itemId !== null && tagId !== null) {
            const ex = DM.find("datatags", d => d.item_id === itemId &&
                d.tag_id === tagId &&
                d.created_by === app.activeUserId &&
                d.code_id === app.activeCode
            )

            try {
                if (ex) {
                    await deleteDataTags([ex.id])
                    toast.success("deleted 1 user tag")
                    times.needsReload("datatags")
                } else {
                    await addDataTags([{
                        tag_id: tagId,
                        item_id: itemId,
                        code_id: app.activeCode,
                        created_by: app.activeUserId,
                        created: Date.now()
                    }])
                    toast.success("added 1 user tag")
                    times.needsReload("datatags")
                }
            } catch (e) {
                console.error(e.toString())
                toast.error("error toggling user tag")
            }
        }
    }

</script>
