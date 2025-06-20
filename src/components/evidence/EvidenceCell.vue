<template>
    <v-sheet :class="['pa-1', invalid ? 'invalid' : '']" :color="highlight ? 'secondary' : 'default'" style="max-width: fit-content;">
        <div class="bg-surface-light" style="position: relative; background-color: #ececec;">
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

            <div @click.stop="onClick" @contextmenu.stop.prevent="onRightClick" @pointermove="onHover" @pointerleave="tt.hide()">
                <video v-if="isVideoFile"
                    class="cursor-pointer pa-0"
                    :src="mediaPath('evidence', item.filepath)"
                    :autoplay="false"
                    :controls="false"
                    playsinline
                    :width="mediaSize"
                    :height="mediaSize"/>

                <v-img v-else
                    class="cursor-pointer"
                    :src="item.filepath ? mediaPath('evidence', item.filepath) : imgUrlS"
                    v-ripple.center
                    :cover="!imageFit"
                    :width="mediaSize"
                    :height="mediaSize"/>
            </div>

            <v-icon v-if="isVideoFile"
                icon="mdi-video"
                density="compact"
                size="small"
                color="secondary"
                class="pa-0"
                style="position: absolute; left: 2px; bottom: 2px; z-index: 3999;"/>

        </div>
        <div v-if="showTag && tagName" class="text-caption text-dots" :style="{ 'max-width': (height-5)+'px' }" :title="tagName">
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
    import { isVideo, mediaPath } from '@/use/utility';
    import { useTooltip } from '@/store/tooltip';

    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const toast = useToast();
    const settings = useSettings();

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        index: {
            type: Number,
            required: false
        },
        evidenceList: {
            type: Array,
            required: false
        },
        highlight: {
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
        showTag: {
            type: Boolean,
            default: true
        },
        showDesc: {
            type: Boolean,
            default: false
        },
        preventClick: {
            type: Boolean,
            default: false
        },
        preventRightClick: {
            type: Boolean,
            default: false
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
        zoomOnHover: {
            type: Boolean,
            default: false
        },
    })

    const emit = defineEmits(["click", "delete", "right-click", "hover"])

    const isVideoFile = computed(() => isVideo(props.item.filepath))
    const invalid = computed(() => props.item.tag_id === null || props.item.tag_id === undefined)

    const mediaSize = computed(() => {
        const fit = !props.showTag && !props.showDesc
        return fit ? props.height : (isVideoFile.value ? props.height-17 : props.height-10)
    })

    const tagName = computed(() => {
        return props.item.tag_id ? DM.getDataItem("tags_name", props.item.tag_id) : null
    })

    function onClick(event) {
        emit("click", props.item, event)
        if (props.preventClick) return
        app.setShowEvidence(props.item.id, props.evidenceList, props.index)
    }
    function onRightClick(event) {
        emit("right-click", props.item)
        if (props.preventRightClick) return;
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
        if (!allowEdit.value) return;

        try {
            await deleteEvidence(props.item.id)
            emit("delete", props.item.id)
            toast.success("deleted evidence");
            times.needsReload("evidence")
        } catch {
            toast.error("error deleting evidence");
        }
    }

    function onHover(event) {
        if (!props.zoomOnHover) return
        const [mx, my] = pointer(event, document.body)

        if (!props.item.filepath) {
            tt.show(
                `<div class="mt-1"><texteara>${props.item.description}</textarea></div>`,
                mx, my
            )
        } else {
            if (isVideoFile.value) {
                tt.show(
                    `<div>
                        <video src="${mediaPath('evidence', props.item.filepath)}" autoplay playsinline controls="false" style="max-height: 250px; max-width: 480px; object-fit: scale-down;"/>
                        ${props.item.description ? '<div class="mt-1"><texteara>'+props.item.description+'</textarea></div>' : ''}
                    </div>`,
                    mx, my
                )
            } else {
                tt.show(
                    `<div>
                        <img src="${mediaPath('evidence', props.item.filepath)}" style="max-height: 250px; max-width: 480px; object-fit: scale-down;"/>
                        ${props.item.description ? '<div class="mt-1"><texteara>'+props.item.description+'</textarea></div>' : ''}
                    </div>`,
                    mx, my
                )
            }
        }
        emit("hover")
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