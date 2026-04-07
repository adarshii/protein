'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, FlaskConical } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SEQUENCE_TYPES, DNA_EXAMPLE, PROTEIN_EXAMPLE } from '@/lib/constants'
import { SequenceType } from '@/lib/types'
import { truncateSequence } from '@/lib/utils'

const schema = z.object({
  sequence: z.string().min(4, 'Sequence must be at least 4 characters').max(50_000, 'Sequence too long'),
  sequenceType: z.nativeEnum(SequenceType),
})

type FormValues = z.infer<typeof schema>

interface SequenceInputProps {
  onSubmit: (values: FormValues) => void
  loading?: boolean
}

export function SequenceInput({ onSubmit, loading = false }: SequenceInputProps) {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { sequenceType: SequenceType.DNA, sequence: '' },
  })

  const sequence = watch('sequence')
  const seqType = watch('sequenceType')

  const loadExample = () => {
    const example = seqType === SequenceType.PROTEIN ? PROTEIN_EXAMPLE : DNA_EXAMPLE
    setValue('sequence', example)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">Sequence Type</label>
        <button
          type="button"
          onClick={loadExample}
          className="text-xs text-primary-600 hover:underline"
        >
          Load example
        </button>
      </div>

      {/* Sequence type selector */}
      <div className="flex gap-2">
        {SEQUENCE_TYPES.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setValue('sequenceType', t.value)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              seqType === t.value
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-slate-600 border-slate-200 hover:border-primary-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Textarea */}
      <div>
        <textarea
          {...register('sequence')}
          rows={6}
          placeholder={`Paste your ${seqType} sequence here…`}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-mono text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
          spellCheck={false}
        />
        {errors.sequence && (
          <p className="mt-1 text-xs text-red-500">{errors.sequence.message}</p>
        )}
        {sequence && (
          <p className="mt-1 text-xs text-slate-400">
            {sequence.length.toLocaleString()} characters · {truncateSequence(sequence, 40)}
          </p>
        )}
      </div>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" /> Analyzing…
          </>
        ) : (
          <>
            <FlaskConical className="w-4 h-4" /> Analyze Sequence
          </>
        )}
      </Button>
    </form>
  )
}
