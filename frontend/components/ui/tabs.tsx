"use client"

import * as TabsPrimitive from "@radix-ui/react-tabs"
import { cn } from "@/lib/utils"

const Tabs = TabsPrimitive.Root

const TabsList = ({
  className,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof TabsPrimitive.List>) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-start rounded-lg bg-slate-100 p-1 text-slate-500",
      className
    )}
    {...props}
  />
)
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = ({
  className,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof TabsPrimitive.Trigger>) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      "disabled:pointer-events-none disabled:opacity-50",
      "data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm",
      className
    )}
    {...props}
  />
)
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = ({
  className,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof TabsPrimitive.Content>) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-4 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
)
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
