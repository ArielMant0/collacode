<template>
    <div class="mr-2 d-flex">
        <div v-if="selected" class="d-flex flex-column align-center justify-center mr-1">
            <v-btn
                :disabled="!allowMoveUp"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-up"
                @click.stop="emit('move-up', item.id)"/>
            <v-btn
                :disabled="!allowMoveDown"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-down"
                @click.stop="emit('move-down', item.id)"/>
        </div>
        <div>
            <v-hover>
                <template v-slot:default="{ props, isHovering }">
                    <v-img v-bind="props"
                        :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                        cover
                        @click.stop="emit('select', item.id)"
                        class="cursor-pointer"
                        gradient="linear-gradient(#f69d3c, #3f87a6)"
                        :width="width"
                        :height="height">

                        <v-overlay v-if="item.teaser"
                            :model-value="isHovering"
                            :key="item.id+'_overlay'"
                            scroll-strategy="reposition"
                            contained class="d-flex align-center justify-center"
                            opacity="0.8"
                            >
                            <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ item.name }}</p>
                        </v-overlay>
                        <v-overlay v-else
                            :model-value="true"
                            persistent
                            scroll-strategy="reposition"
                            :key="item.id+'_overlay_p'"
                            contained class="d-flex align-center justify-center"
                            :opacity="isHovering ? 0.8 : 0.5"
                            >
                            <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ item.name }}</p>
                        </v-overlay>
                    </v-img>
                </template>
            </v-hover>
        </div>
    </div>

    <v-sheet v-for="e in evidence"
        class="pa-1 mr-2"
        :width="openEvidence.has(e.id) ? width*scaleFactor : height">

        <v-hover v-if="e.filepath">
            <template v-slot:default="{ isHovering, props }">
                <v-img v-bind="props"
                    class="cursor-pointer"
                    :src="'evidence/'+e.filepath"
                    cover
                    @click.stop="emit('enlarge', e)"
                    v-ripple.center
                    :width="openEvidence.has(e.id) ? width*scaleFactor : height-10"
                    :height="openEvidence.has(e.id) ? height*scaleFactor : height-10">
                    <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                        <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                    </v-overlay>
                </v-img>
            </template>
        </v-hover>
        <div v-else>
            <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
        </div>

        <div>
            <div class="d-flex">
                <v-btn
                    :icon="openEvidence.has(e.id) ? 'mdi-menu-up' : 'mdi-menu-down'"
                    density="compact"
                    rounded="sm"
                    @click.stop="emit('evidence', e.id)"
                    variant="flat"/>
                <div v-if="e.tag" class="text-caption text-dots" style="max-width: 100%;">{{ e.tag.name }}</div>
            </div>
            <v-card v-if="openEvidence.has(e.id)" density="compact" style="width: 100%">
                <v-card-text class="pa-0">
                    <v-textarea
                        readonly
                        :rows="e.rows + 1"
                        class="tiny-font text-caption"
                        :model-value="e.description"
                        hide-details hide-spin-buttons/>
                </v-card-text>
            </v-card>
        </div>
    </v-sheet>
</template>

<script setup>

    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        evidence: {
            type: Array,
            default: () => ([])
        },
        selected: {
            type: Boolean,
            default: false
        },
        openEvidence: {
            type: Set,
            required: true
        },
        allowMoveUp: {
            type: Boolean,
            default: false
        },
        allowMoveDown: {
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
        scaleFactor: {
            type: Number,
            default: 4
        },
    })
    const emit = defineEmits(["move-down", "move-up", "evidence", "select", "enlarge"])
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