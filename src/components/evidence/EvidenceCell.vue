<template>
    <v-sheet :class="['pa-1', invalid ? 'invalid' : '']" :color="selected ? 'secondary' : 'default'">
        <div class="bg-surface-light" style="position: relative; background-color: #ececec;" :title="item.description">
            <v-btn v-if="allowEdit && allowCopy"
                icon="mdi-content-copy"
                density="comfortable"
                size="small"
                class="primary-on-hover"
                @click="copyEvidence"
                style="position: absolute; right: 24px; top: -8px; z-index: 3999;"/>
            <v-btn v-if="allowEdit && allowDelete"
                icon="mdi-close"
                density="comfortable"
                size="small"
                class="red-on-hover pa-0"
                @click="deleteEv"
                style="position: absolute; right: -8px; top: -8px; z-index: 3999;"/>

            <video v-if="isVideo"
                class="cursor-pointer pa-0"
                :src="mediaPath('evidence', item.filepath)"
                @click.stop="emit('select', item)"
                @contextmenu.stop="onRightClick"
                :autoplay="false"
                :controls="false"
                playsinline
                :width="height-17"
                :height="height-17"/>

            <v-img v-else
                class="cursor-pointer"
                :src="item.filepath ? mediaPath('evidence', item.filepath) : imgUrlS"
                @click.stop="emit('select', item)"
                @contextmenu.stop="onRightClick"
                v-ripple.center
                :cover="!imageFit"
                :width="height-10"
                :height="height-10"/>

            <v-icon v-if="isVideo"
                icon="mdi-video"
                density="compact"
                size="small"
                color="secondary"
                class="pa-0"
                style="position: absolute; left: 2px; bottom: 2px; z-index: 3999;"/>

        </div>
        <div v-if="tagName" class="text-caption text-dots" :style="{ 'max-width': (height-5)+'px' }" :title="tagName">
            {{ tagName }}
        </div>
        <div v-if="showDesc && props.item.description" class="text-caption text-ww" :style="{ 'max-width': (height-5)+'px' }">
            {{ props.item.description.length > maxDesc ? props.item.description.slice(0, maxDesc)+'..' : props.item.description }}
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
    import { deleteEvidence } from '@/use/data-api';
    import { storeToRefs } from 'pinia';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import DM from '@/use/data-manager';
    import { mediaPath } from '@/use/utility';

    const app = useApp()
    const times = useTimes()
    const toast = useToast();
    const settings = useSettings();

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        selected: {
            type: Boolean,
            default: false
        },
        allowDelete: {
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
        },
        maxDesc: {
            type: Number,
            default: 80
        },
    })
    const emit = defineEmits(["select", "delete", "right-click"])

    const isVideo = computed(() => props.item.filepath && props.item.filepath.endsWith("mp4"))
    const invalid = computed(() => props.item.tag_id === null || props.item.tag_id === undefined)

    const tagName = computed(() => {
        return props.item.tag_id ? DM.getDataItem("tags_name", props.item.tag_id) : null
    })

    function onRightClick(event) {
        emit("right-click", props.item)
        event.preventDefault();
        if (props.disableContextMenu) return;
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "evidence", props.item.id,
            mx, my,
            null,
            {
                item: props.item.item_id,
                tag: props.item.tag_id
            },
            CTXT_OPTIONS.evidence
        );
    }

    function copyEvidence() {
        app.toggleAddEvidence(props.item.item_id, null, props.item.filepath)
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