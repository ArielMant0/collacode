<template>
    <v-sheet class="pa-1" :color="selected ? 'secondary' : 'default'">
        <div style="position: relative; background-color: #ececec;" :title="item.description">
            <v-btn v-if="allowCopy"
                icon="mdi-content-copy"
                density="comfortable"
                size="small"
                class="primary-on-hover"
                @click="copyEvidence"
                style="position: absolute; right: 24px; top: -8px; z-index: 3999;"/>
            <v-btn v-if="allowEdit"
                icon="mdi-close"
                density="comfortable"
                size="small"
                class="red-on-hover pa-0"
                @click="deleteEv"
                style="position: absolute; right: -8px; top: -8px; z-index: 3999;"/>
            <v-img
                class="cursor-pointer"
                :src="item.filepath ? 'evidence/'+item.filepath : imgUrlS"
                @click.stop="emit('select', item)"
                @contextmenu.stop="onRightClick"
                v-ripple.center
                :cover="!imageFit"
                :width="height-10"
                :height="height-10"/>
        </div>
        <div v-if="tagName" class="text-caption text-dots" :style="{ 'max-width': (height-5)+'px' }" :title="tagName">
            {{ tagName }}
        </div>
        <div v-if="showDesc && props.item.description" class="text-caption text-ww" :style="{ 'max-width': (height-5)+'px' }">
            {{ props.item.description.length > 100 ? props.item.description.slice(0, 100)+'..' : props.item.description }}
        </div>
    </v-sheet>
</template>

<script setup>

    import { pointer } from 'd3';
    import { computed } from 'vue';
    import { useToast } from "vue-toastification";
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { deleteEvidence } from '@/use/utility';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const app = useApp()
    const times = useTimes()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowedTags: {
            type: Array,
            required: true
        },
        selected: {
            type: Boolean,
            default: false
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
        allowCopy: {
            type: Boolean,
            default: false
        },
        showDesc: {
            type: Boolean,
            default: false
        },
        disableContextMenu: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 80
        },
        imageFit: {
            type: Boolean,
            default: true
        }
    })
    const emit = defineEmits(["select", "delete", "right-click"])

    const toast = useToast();
    const settings = useSettings();

    const tagName = computed(() => {
        if (props.item.tag_id && props.allowedTags.length > 0) {
            const tag = props.allowedTags.find(d => d.id === props.item.tag_id);
            return tag ? tag.name : null
        }
        return null
    })

    function onRightClick(event) {
        emit("right-click", props.item)
        event.preventDefault();
        if (props.disableContextMenu) return;
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "evidence", props.item.id,
            mx + 15,
            my + 15,
            { game: props.item.game_id, tag: props.item.tag_id },
            CTXT_OPTIONS.evidence.concat(CTXT_OPTIONS.externalization_add)
        );
    }

    function copyEvidence() {
        app.toggleAddEvidence(props.item.game_id, null, props.item.filepath)
    }

    async function deleteEv() {
        if (!props.allowEdit) return;

        try {
            await deleteEvidence(props.item.id)
            emit("delete", props.item.id)
            toast.success("deleted evidence");
            times.needsReload("evidence")
        } catch {
            toast.error("error deleting evidence");
        }
    }

</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
.tiny-font {
    font-size: 10px;
    max-height: 200px;
}
</style>