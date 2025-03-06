"use client";
import { useState, useEffect, Fragment } from "react";
import { useRouter } from "next/navigation";
import { Dialog, Transition } from "@headlessui/react";
import { DatePicker } from "@heroui/react";
import { CalendarDate, parseDate } from "@internationalized/date";

export default function Dashboard() {
  const [showModal, setShowModal] = useState(true);
  const [startDate, setStartDate] = useState<CalendarDate | null>(null);
  const [selectedDate, setSelectedDate] = useState<CalendarDate | null>(null);
  const router = useRouter();

  const handleConfirm = async () => {
    setStartDate(selectedDate);
    setShowModal(false);
    await fetch("/api/save-start-date", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ start_date: selectedDate?.toString() }),
    });
    await fetch("/api/fetch-emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: "your_user_id_here" }), // Replace with actual user ID
    });
    router.replace("/processing");
  };

  return (
    <div className="flex flex-col items-center justify-center text-center pt-64">
      {/* Modal */}
      <Transition appear show={showModal} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setShowModal(false)}>
          <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm" />
          <div className="fixed inset-0 flex items-center justify-center">
            <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
              <h2 className="text-xl font-semibold text-black">
                Please enter the start date of your current job search:
              </h2>
              <DatePicker
                className="mt-4 w-full p-2 border rounded-lg"
                value={selectedDate}
                onChange={(date) => setSelectedDate(date as CalendarDate)}
              />
              <button
                className="mt-4 w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
                onClick={handleConfirm}
              >
                Confirm
              </button>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Dashboard */}
      {!showModal && (
        <>
          <h1 className="text-3xl font-bold text-blue-500">Dashboard</h1>
          <p className="pt-8">Your job search start date: {startDate ? startDate.toString() : "Not set"}</p>
        </>
      )}
    </div>
  );
}